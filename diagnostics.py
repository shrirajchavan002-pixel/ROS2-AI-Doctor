import os
import platform
import subprocess
import xml.etree.ElementTree as ET
import re

# Performance optimization: cache the deep scan to avoid double scanning
_cached_scan_results = None

def find_ros2_workspace():
    current = os.getcwd()
    while current != "/":
        if os.path.isdir(os.path.join(current, "src")):
            return current
        current = os.path.dirname(current)
    return os.getcwd()

def deep_workspace_scan(force=False):
    global _cached_scan_results
    if _cached_scan_results is not None and not force:
        return _cached_scan_results
        
    ws_path = find_ros2_workspace()
    src_path = os.path.join(ws_path, "src")
    results = []
    
    # 10. Validate Environment
    env_vars = ['ROS_DISTRO', 'AMENT_PREFIX_PATH', 'CMAKE_PREFIX_PATH', 'COLCON_PREFIX_PATH', 'PYTHONPATH']
    for var in env_vars:
        if var in os.environ:
            results.append({"type": "success", "msg": f"Environment {var} is set."})
        else:
            results.append({"type": "error", "msg": f"Missing Environment Variable: {var}"})

    # 9. Validate Build Folder
    for d in ["build", "install", "log"]:
        d_path = os.path.join(ws_path, d)
        if os.path.isdir(d_path):
            results.append({"type": "success", "msg": f"Found {d}/ directory."})
            if d == "install" and not os.path.isfile(os.path.join(d_path, "setup.bash")):
                results.append({"type": "error", "msg": "install/setup.bash is missing. Build may be incomplete."})
        else:
            results.append({"type": "warning", "msg": f"Missing {d}/ directory (Package might not be built)."})

    if not os.path.exists(src_path):
        results.append({"type": "error", "msg": "No 'src' directory found. STATUS: NOT VERIFIED"})
        _cached_scan_results = results
        return results

    # 15. Recursive Deep Scan for Packages
    for root, dirs, files in os.walk(src_path):
        if "package.xml" in files:
            pkg_name = os.path.basename(root)
            results.append({"type": "success", "msg": f"Found Package: {pkg_name}"})
            
            xml_deps = set()
            xml_test_deps = set()
            cmake_deps = set()
            py_deps = set()
            cpp_deps = set()
            is_python_pkg = "setup.py" in files
            is_cmake_pkg = "CMakeLists.txt" in files
            
            # 1. Parse package.xml
            try:
                tree = ET.parse(os.path.join(root, "package.xml"))
                xml_root = tree.getroot()
                parsed_name = xml_root.findtext('name')
                if parsed_name != pkg_name:
                    results.append({"type": "error", "msg": f"[{pkg_name}] XML name '{parsed_name}' mismatch."})
                
                for dep_tag in ['buildtool_depend', 'build_depend', 'exec_depend', 'depend']:
                    for dep in xml_root.findall(dep_tag):
                        if dep.text: xml_deps.add(dep.text.strip())
                        
                for dep in xml_root.findall('test_depend'):
                    if dep.text: xml_test_deps.add(dep.text.strip())
                
                if not xml_root.findall('buildtool_depend'):
                    results.append({"type": "error", "msg": f"[{pkg_name}] Missing <buildtool_depend> in package.xml"})
                else:
                    results.append({"type": "success", "msg": f"[{pkg_name}] package.xml parsed successfully."})
                    
            except Exception as e:
                results.append({"type": "error", "msg": f"[{pkg_name}] Invalid package.xml: {e}"})

            # 2. Parse CMakeLists.txt
            if is_cmake_pkg:
                try:
                    with open(os.path.join(root, "CMakeLists.txt"), "r") as f:
                        content = f.read()
                        cmake_deps.update(re.findall(r'find_package\s*\(\s*([a-zA-Z0-9_]+)', content))
                        
                        if 'ament_package' not in content:
                            results.append({"type": "error", "msg": f"[{pkg_name}] Missing ament_package() in CMakeLists."})
                        if 'install(' not in content:
                            results.append({"type": "warning", "msg": f"[{pkg_name}] Missing install() targets."})
                        results.append({"type": "success", "msg": f"[{pkg_name}] CMakeLists.txt parsed successfully."})
                except Exception:
                    results.append({"type": "error", "msg": f"[{pkg_name}] Failed to read CMakeLists.txt. NOT VERIFIED."})

            # 3. Parse setup.py & 4. Parse setup.cfg
            if is_python_pkg:
                try:
                    with open(os.path.join(root, "setup.py"), "r") as f:
                        content = f.read()
                        if 'console_scripts' not in content:
                            results.append({"type": "warning", "msg": f"[{pkg_name}] Missing console_scripts in setup.py"})
                    if "setup.cfg" in files:
                        with open(os.path.join(root, "setup.cfg"), "r") as f:
                            if 'script_dir' not in f.read():
                                results.append({"type": "warning", "msg": f"[{pkg_name}] setup.cfg missing script_dir settings."})
                    results.append({"type": "success", "msg": f"[{pkg_name}] setup.py & setup.cfg parsed."})
                except Exception:
                    pass

            # 5. Scan Python Nodes & 6. Scan C++ Nodes
            for d_root, d_dirs, d_files in os.walk(root):
                # Python Nodes
                for f in d_files:
                    if f.endswith('.py'):
                        py_path = os.path.join(d_root, f)
                        
                        # False Positive Avoidance: Identify skips
                        is_test_dir = 'test' in d_root.split(os.sep) or 'tests' in d_root.split(os.sep)
                        is_test_file = f.startswith('test_') or f.endswith('_test.py')
                        is_init = f == '__init__.py'
                        
                        if is_init:
                            results.append({"type": "skipped", "msg": f"[{pkg_name}] {f}", "reason": "Package initializer"})
                            continue
                            
                        if is_test_dir or is_test_file:
                            reason = "ROS2 template test" if f in ['test_flake8.py', 'test_pep257.py', 'test_copyright.py'] else "Test file"
                            results.append({"type": "skipped", "msg": f"[{pkg_name}] {f}", "reason": reason})
                            
                            # Check pytest dependency for tests
                            try:
                                with open(py_path, "r") as py_f:
                                    content = py_f.read()
                                    if 'pytest' in content or 'import pytest' in content:
                                        if 'pytest' not in xml_test_deps and 'python3-pytest' not in xml_test_deps:
                                            results.append({"type": "warning", "msg": f"[{pkg_name}] {f} imports pytest but <test_depend>pytest</test_depend> is missing in package.xml"})
                            except Exception:
                                pass
                            continue # Skip lifecycle verification
                        
                        # Regular Python executable nodes
                        try:
                            with open(py_path, "r") as py_f:
                                content = py_f.read()
                                
                                imports = re.findall(r'^(?:from|import)\s+([a-zA-Z0-9_]+)', content, re.MULTILINE)
                                py_deps.update(imports)
                                
                                # Validate ROS2 lifecycle ONLY if it imports rclpy or has Node/main
                                if 'rclpy' in imports or 'rclpy' in content or 'Node' in content:
                                    if 'rclpy.init' not in content and 'main' in content:
                                        results.append({"type": "error", "msg": f"[{pkg_name}] {f} missing rclpy.init()"})
                                    if 'shutdown' not in content:
                                        results.append({"type": "warning", "msg": f"[{pkg_name}] {f} missing rclpy.shutdown()"})
                        except Exception:
                            pass
                            
                # C++ Nodes
                for f in d_files:
                    if f.endswith('.cpp') or f.endswith('.hpp'):
                        cpp_path = os.path.join(d_root, f)
                        try:
                            with open(cpp_path, "r") as cpp_f:
                                content = cpp_f.read()
                                if 'rclcpp::init' not in content and 'main' in content:
                                    results.append({"type": "error", "msg": f"[{pkg_name}] {f} missing rclcpp::init()"})
                                includes = re.findall(r'#include\s*[<"]([^/]+)', content)
                                cpp_deps.update(includes)
                        except Exception:
                            pass
                            
                # 7. Scan Launch Files
                if 'launch' in d_dirs or d_root.endswith('launch'):
                    results.append({"type": "success", "msg": f"[{pkg_name}] Launch directory verified."})

            # 8. Scan Interfaces
            has_interfaces = any(d in dirs for d in ['msg', 'srv', 'action'])
            if has_interfaces:
                results.append({"type": "success", "msg": f"[{pkg_name}] Custom interfaces (msg/srv) detected."})
                if is_cmake_pkg and 'rosidl_generate_interfaces' not in ''.join(open(os.path.join(root, "CMakeLists.txt")).readlines()):
                    results.append({"type": "error", "msg": f"[{pkg_name}] Missing rosidl_generate_interfaces in CMakeLists."})

            # 11 & 12. Cross Validation & Intelligent Dependency Checker
            standard_libs = {'os', 'sys', 'time', 'math', 'rclpy', 'rclcpp', 'std_msgs', 'unittest', 'pytest'}
            
            if is_cmake_pkg:
                for dep in cmake_deps:
                    if dep not in xml_deps and dep not in xml_test_deps and dep not in ['ament_cmake']:
                        results.append({"type": "error", "msg": f"[{pkg_name}] Cross-Validation: '{dep}' in CMakeLists but missing in package.xml"})
            
            for dep in py_deps:
                if dep not in standard_libs and dep not in xml_deps and dep not in xml_test_deps and dep != pkg_name:
                    results.append({"type": "warning", "msg": f"[{pkg_name}] Dependency '{dep}' imported in Python but not in package.xml"})
                    
            for dep in cpp_deps:
                if dep not in standard_libs and dep not in xml_deps and dep not in xml_test_deps and dep != pkg_name:
                    results.append({"type": "warning", "msg": f"[{pkg_name}] Dependency '{dep}' included in C++ but not in package.xml"})

    if not any(r['type'] == 'success' and 'Found Package' in r['msg'] for r in results):
        results.append({"type": "warning", "msg": "No ROS2 packages found inside src/ directory."})
        
    _cached_scan_results = results
    return results

def get_workspace_health(ws_path):
    health = {
        'ros_distro': os.environ.get('ROS_DISTRO', 'NOT VERIFIED'),
        'python_version': platform.python_version(),
        'workspace_found': os.path.isdir(os.path.join(ws_path, "src")),
        'components': {
            'Python Env': 100,
            'ROS Env': 100,
            'Workspace Info': 100,
            'Dependencies': 100, 
            'Interfaces': 100, 
            'Colcon Build': 100
        }
    }
    
    try:
        subprocess.run(['colcon', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        health['components']['Colcon Build'] = 0

    try:
        subprocess.run(['ros2', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        health['components']['ROS Env'] = 0

    if health['ros_distro'] == 'NOT VERIFIED':
        health['components']['ROS Env'] = max(0, health['components']['ROS Env'] - 50)

    if not health['workspace_found']:
        health['components']['Workspace Info'] = 0
        health['components']['Dependencies'] = 0
        health['components']['Interfaces'] = 0
    else:
        if not os.path.isdir(os.path.join(ws_path, "build")):
            health['components']['Workspace Info'] -= 20
        if not os.path.isdir(os.path.join(ws_path, "install")):
            health['components']['Workspace Info'] -= 20

    # Dynamic Health Adjustment based on deep scan evidence
    scan_results = deep_workspace_scan()
    errors = [r for r in scan_results if r['type'] == 'error']
    warnings = [r for r in scan_results if r['type'] == 'warning']
    
    for e in errors:
        if 'Dependency' in e['msg'] or 'Missing <buildtool_depend>' in e['msg'] or 'package.xml' in e['msg']:
            health['components']['Dependencies'] = max(0, health['components']['Dependencies'] - 15)
        elif 'missing rclpy' in e['msg'] or 'missing rclcpp' in e['msg']:
            health['components']['Python Env'] = max(0, health['components']['Python Env'] - 15)
        elif 'Interfaces' in e['msg'] or 'rosidl' in e['msg']:
            health['components']['Interfaces'] = max(0, health['components']['Interfaces'] - 20)
        else:
            health['components']['Workspace Info'] = max(0, health['components']['Workspace Info'] - 10)
            
    for w in warnings:
        if 'Dependency' in w['msg'] or 'missing script_dir' in w['msg']:
            health['components']['Dependencies'] = max(0, health['components']['Dependencies'] - 5)
        elif 'missing rclpy.shutdown' in w['msg'] or 'console_scripts' in w['msg']:
            health['components']['Python Env'] = max(0, health['components']['Python Env'] - 5)
        else:
            health['components']['Workspace Info'] = max(0, health['components']['Workspace Info'] - 5)

    scores = list(health['components'].values())
    overall = sum(scores) // len(scores)
    
    # Absolute strict rule: Never display 100% if errors or warnings exist
    if (errors or warnings) and overall == 100:
        overall = 99
        
    health['overall_score'] = overall
    return health

def run_doctor():
    ws = find_ros2_workspace()
    return get_workspace_health(ws)

def scan_workspace_files():
    results = deep_workspace_scan()
    # Exclude skipped files from AI context to save tokens, AI doesn't need to read skipped files.
    summary = "\n".join([f"[{r['type'].upper()}] {r['msg']}" for r in results if r['type'] != 'skipped'])
    return summary

def generate_tree():
    ws = find_ros2_workspace()
    try:
        res = subprocess.run(['tree', '-L', '3', ws], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout
    except FileNotFoundError:
        return "Tree command not installed. Use 'sudo apt install tree'."
    return "Could not generate tree."

def get_error_database_context():
    return """
    [ROS2 ERROR CLASSIFICATION DATABASE]:
    - ModuleNotFoundError: Likely missing install folder, unsourced workspace, or missing package.xml dep.
    - CMake Error find_package: package not built, misspelled, or missing ament_target_dependencies.
    - Executable not found: Missing console_scripts in setup.py or install() in CMakeLists.txt.
    - rosidl_generate_interfaces: Missing msg/srv mapping or missing rosidl_default_generators.
    """
