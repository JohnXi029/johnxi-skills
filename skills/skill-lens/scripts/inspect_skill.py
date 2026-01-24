#!/usr/bin/env python3
import sys
import re
import pathlib

class SkillLensScanner:
    def __init__(self, skill_path):
        self.skill_dir = pathlib.Path(skill_path).resolve()
        self.report = []

    def log(self, text):
        self.report.append(text)

    def scan(self):
        if not self.skill_dir.is_dir():
            return f"Error: {self.skill_dir} is not a directory."

        self.log(f"# Raw Analysis Data: {self.skill_dir.name}\n")
        
        self._scan_file_manifest()
        self._scan_tech_depth()
        self._scan_configs()
        
        return "\n".join(self.report)

    def _scan_file_manifest(self):
        self.log("## 1. Raw File Manifest Data (For Tree Generation)")
        
        # 遍历目录结构，按树状逻辑提供数据
        for folder in [".", "scripts", "references", "assets"]:
            path = self.skill_dir if folder == "." else self.skill_dir / folder
            if not path.is_dir(): continue

            files = [f for f in path.iterdir() if f.is_file() and not f.name.startswith(".")]
            if not files: continue

            folder_display = "ROOT" if folder == "." else folder
            self.log(f"### DIR: {folder_display}")
            
            for f in sorted(files, key=lambda x: x.name):
                summary = self._get_file_summary(f)
                self.log(f"- FILE: {f.name} | DESC: {summary}")
        self.log("")

    def _get_file_summary(self, path):
        # 根据文件名或后缀提供智能描述
        name = path.name
        ext = path.suffix

        if name == "SKILL.md": return "Main Skill definition and instructions."
        if name == "README.md": return "Project overview and documentation."
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                # 只读取前 500 字符进行分析
                content = f.read(500)
                
                # 针对脚本的描述提取
                if ext in [".py", ".js", ".ts", ".sh"]:
                    doc = re.search(r'["\']{3}(.*?)["\']{3}', content, re.DOTALL)
                    if doc: return doc.group(1).strip().split('\n')[0][:100]
                    first_line = content.split('\n')[0]
                    if first_line.startswith("#"): return first_line.replace("#", "").strip()[:100]
                
                # 针对 Markdown 的标题提取
                if ext == ".md":
                    title = re.search(r'^#\s+(.*)', content, re.MULTILINE)
                    if title: return f"Doc: {title.group(1).strip()[:100]}"

                return f"Asset file ({ext[1:] if ext else 'no ext'})"
        except:
            return "File exists (unreadable)"

    def _scan_tech_depth(self):
        scripts_dir = self.skill_dir / "scripts"
        if not scripts_dir.is_dir(): return

        self.log("## 2. Technical Depth Analysis (Scripts Only)")
        for script_file in scripts_dir.iterdir():
            if script_file.is_file() and not script_file.name.startswith("."):
                self._analyze_script_tech(script_file)

    def _analyze_script_tech(self, path):
        ext = path.suffix
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except: return

        self.log(f"### Script: {path.name}")
        deps = []
        if ext == ".py":
            deps = re.findall(r"^(?:import|from)\s+([a-zA-Z0-9_]+)", content, re.MULTILINE)
        elif ext in [".js", ".ts", ".tsx"]:
            deps = re.findall(r"(?:import|require)\s*\(?['\"]([@a-zA-Z0-9\-_/]+)['\"]", content)
        
        if deps: self.log(f"- **Dependencies**: {', '.join(sorted(list(set(deps))))}")
        
        markers = []
        if "async " in content: markers.append("Asynchronous")
        if "class " in content: markers.append("OO-Pattern")
        if markers: self.log(f"- **Markers**: {', '.join(markers)}")

    def _scan_configs(self):
        self.log("\n## 3. Environment & Configuration")
        configs = ["package.json", "requirements.txt", "Dockerfile", "Makefile"]
        found = [cfg for cfg in configs if (self.skill_dir / cfg).exists()]
        if found:
            for f in found: self.log(f"- Found **{f}**")
        else:
            self.log("- No standard environment configs found.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 inspect_skill.py <skill_directory_path>")
        sys.exit(1)
    
    scanner = SkillLensScanner(sys.argv[1])
    print(scanner.scan())

if __name__ == "__main__":
    main()
