import sys
import subprocess
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live
from rich.table import Table

from ai_engine import analyze_error, extract_command
from diagnostics import run_doctor, generate_tree, deep_workspace_scan, scan_workspace_files
from history import save_to_history, export_reports, init_db

console = Console()

def display_menu():
    console.print("\n[bold green]🧬 --- ROS2 AI Doctor Pro --- 🧬[/]")
    console.print("  [1] 🚀 Analyze Error & Auto-Fix")
    console.print("  [2] 🩺 Deep Workspace Scan & Health Check")
    console.print("  [3] 🌳 View Project Tree")
    console.print("  [4] 💾 Export AI Reports & Logs")
    console.print("  [5] ❌ Exit")
    
    try:
        return Prompt.ask("\n[bold yellow]Select a professional action[/]", choices=["1", "2", "3", "4", "5"], default="1")
    except (KeyboardInterrupt, EOFError):
        console.print("\n\n[bold red]🛑 Exit request received! Goodbye![/]")
        sys.exit(0)

def perform_auto_checks():
    console.print("\n[bold cyan]🔬 Running Professional Deep Workspace Scanner...[/]")
    
    # Calling the cached scanner
    results = deep_workspace_scan(force=True)
    
    success_flags = set()
    warnings_list = []
    errors_list = []
    skipped_list = []
    scan_context = ""
    
    for res in results:
        if res['type'] != 'skipped':
            scan_context += f"[{res['type'].upper()}] {res['msg']}\n"
            
        if res['type'] == 'success':
            if 'Environment' in res['msg']: success_flags.add("Environment Variables")
            if 'package.xml parsed' in res['msg']: success_flags.add("package.xml")
            if 'CMakeLists.txt parsed' in res['msg']: success_flags.add("CMakeLists.txt")
            if 'setup.py' in res['msg']: success_flags.add("setup.py / setup.cfg")
            if 'Launch' in res['msg']: success_flags.add("Launch Files")
            if 'Interfaces' in res['msg']: success_flags.add("Custom Interfaces")
        elif res['type'] == 'warning':
            warnings_list.append(res['msg'])
        elif res['type'] == 'error':
            errors_list.append(res['msg'])
        elif res['type'] == 'skipped':
            skipped_list.append({"msg": res['msg'], "reason": res['reason']})

    # Display Professional Report UI
    console.print("\n[bold green]Workspace Scan[/]")
    for item in sorted(success_flags):
        console.print(f"  [green]✓[/] {item}")
        time.sleep(0.02)
        
    if skipped_list:
        console.print("\n[bold blue]Skipped Files (Ignored for ROS2 Lifecycle)[/]")
        for skip in skipped_list:
            console.print(f"  [blue]✓[/] {skip['msg']}")
            console.print(f"      [dim]Reason: {skip['reason']}[/dim]")
            time.sleep(0.01)
            
    if warnings_list or errors_list:
        console.print("\n[bold yellow]Scanner Warnings & Errors[/]")
        for err in errors_list:
            console.print(f"  [red]✗[/] {err}")
            time.sleep(0.02)
        for warn in warnings_list:
            console.print(f"  [yellow]![/] {warn}")
            time.sleep(0.02)
    else:
        console.print("\n[bold green]✓ No Cross-Validation Errors Found![/]")

    return scan_context

def handle_analyze():
    scan_context = perform_auto_checks()
    
    console.print("\n[bold cyan]📥 Paste your ROS2/Colcon error below.[/]")
    console.print("[bold yellow](When finished, type 'DONE' on a new line and press Enter):[/]")
    lines = []
    try:
        while True:
            line = input()
            if line.strip().upper() == "DONE": 
                break
            lines.append(line)
    except KeyboardInterrupt: 
        console.print("\n[yellow]Input cancelled.[/]")
        return
    except EOFError:
        pass
        
    error_text = "\n".join(lines).strip()
    if not error_text: return
    
    with Live(Spinner("dots", text="[bold cyan]AI Doctor is diagnosing evidence and calculating confidence...[/]"), refresh_per_second=10):
        analysis = analyze_error(error_text, scan_context)
        save_to_history(error_text, analysis)
        
    console.print(Panel(Markdown(analysis), title="[bold green]🧬 Evidence-Based AI Diagnosis[/]", border_style="green"))
    
    suggested_cmd = extract_command(analysis)
    if suggested_cmd:
        console.print(f"\n[bold yellow]💡 Safe Recovery Commands Generated:[/] \n[italic cyan]{suggested_cmd}[/]")
        choice = Prompt.ask("\n[bold]Do you want to run these commands automatically now?[/]", choices=["y", "n"], default="n")
        
        if choice == "y":
            console.print(f"[cyan]⚙️ Executing Recovery Plan...[/]")
            try:
                result = subprocess.run(suggested_cmd, shell=True, check=True, text=True, capture_output=True, executable='/bin/bash')
                console.print(f"[bold green]✅ Success! Workspace recovered.[/]\n[dim]{result.stdout}[/]")
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]❌ Command Failed![/]\n[dim]{e.stderr}[/]")

def main():
    init_db()
    while True:
        choice = display_menu()
        
        if choice == "1": 
            handle_analyze()
            
        elif choice == "2":
            perform_auto_checks()
            health = run_doctor()
            
            table = Table(title="🩺 Professional Workspace Health Report", show_header=True, header_style="bold cyan")
            table.add_column("System Component", style="cyan")
            table.add_column("Health Status", justify="right", style="magenta")
            
            for component, score in health['components'].items():
                color = "green" if score == 100 else "yellow" if score >= 50 else "red"
                table.add_row(component, f"[{color}]{score}%[/{color}]")
            
            console.print(table)
            overall = health['overall_score']
            color_overall = "bold green" if overall >= 90 else "bold yellow" if overall >= 70 else "bold red"
            console.print(f"\n[bold]Overall Health Score:[/] [{color_overall}]{overall}/100[/]\n")
            
        elif choice == "3":
            console.print("\n[bold cyan]🌳 Advanced Project Structure:[/]\n")
            console.print(generate_tree())
            
        elif choice == "4":
            filename, msg = export_reports()
            console.print(f"[green]{msg}[/]")
            console.print(f"[dim]Note: Detailed JSON and MD logs are also automatically saved in ~/ros2_error_explainer/logs/[/]")
            
        elif choice == "5": 
            console.print("[bold green]Goodbye![/]")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold red]🛑 Emergency Stop Activated![/]")
        sys.exit(0)
