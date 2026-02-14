import os
import sys

from roadmap_prompt import generate_roadmap

MODULES_DIR = r"F:\KNOUX_OS_Guardian\src\modules"


# تقييمات بسيطة لكل Module (يمكن تعديلها لاحقًا)
def assess_module(module_name: str) -> dict:
    # جاهزية، تعقيد، خطر: 1-5
    return {
        "readiness": 4,
        "complexity": 3,
        "risk": 2,
    }


# قراءة جميع الموديلات من src/modules
def list_modules() -> list:
    modules = [
        d for d in os.listdir(MODULES_DIR)
        if os.path.isdir(os.path.join(MODULES_DIR, d)) and not d.startswith("__")
    ]
    return sorted(modules)


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    modules = list_modules()

    for module in modules:
        safe_print(f"\n\nModule: {module}")
        safe_print("=" * 60)

        roadmap = generate_roadmap(module)
        assessment = assess_module(module)

        for phase, desc in roadmap.items():
            safe_print(f"{phase}:\n{desc}\n{'-' * 50}")

        safe_print(
            "Assessment: "
            f"Readiness={assessment['readiness']}/5 | "
            f"Complexity={assessment['complexity']}/5 | "
            f"Risk={assessment['risk']}/5"
        )
        safe_print("~" * 60)
