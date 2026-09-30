import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from semantic.embedder import MiniLMEmbedder
from semantic.alignment import AlignmentEngine

CASES = [
    ("WATCH A CDRAMA", [
        ("relevant", "youtube.com | Chinese Drama Episode - Romantic C-Drama Full Episode"),
        ("relevant", "viki.com | Chinese Dramas - Romance, Comedy & C-Drama Series"),
        ("relevant", "netflix.com | Chinese Romantic Drama Series"),
        ("relevant", "youtube.com | C-Drama Recommendations - Best Chinese Romance Dramas"),
        ("irrelevant", "youtube.com | MrBeast latest challenge video"),
        ("irrelevant", "instagram.com | Random celebrity reels"),
        ("irrelevant", "netflix.com | Action Movies and Thrillers"),
    ]),
    ("WATCH A 2 HOUR QUANTUM MECHANICS LECTURE", [
        ("relevant", "youtube.com | Quantum Mechanics Full Lecture - 2 Hours"),
        ("relevant", "coursera.org | Quantum Mechanics Lecture - Wave Functions"),
        ("relevant", "youtube.com | Schrödinger Equation Explained"),
        ("relevant", "mit.edu | Quantum Mechanics Course Lecture Notes"),
        ("irrelevant", "youtube.com | MrBeast latest challenge"),
        ("irrelevant", "instagram.com | Celebrity reels"),
        ("irrelevant", "netflix.com | Romantic Comedy Movies"),
    ]),
    ("FINISH MY PYTHON HOMEWORK", [
        ("relevant", "code | assignment.py - Visual Studio Code"),
        ("relevant", "stackoverflow.com | Python recursion error"),
        ("relevant", "github.com | Python homework assignment"),
        ("relevant", "youtube.com | Python debugging tutorial"),
        ("irrelevant", "instagram.com | Funny reels"),
        ("irrelevant", "netflix.com | New releases and movies"),
        ("irrelevant", "youtube.com | Celebrity interview"),
    ]),
    ("MAKE BUTTER CHICKEN FOR DINNER", [
        ("relevant", "youtube.com | Easy Butter Chicken Recipe"),
        ("relevant", "google.com | Butter Chicken Recipe - Ingredients and Instructions"),
        ("relevant", "reddit.com | Best homemade butter chicken recipe"),
        ("relevant", "youtube.com | Indian Butter Chicken Step-by-Step Cooking"),
        ("irrelevant", "instagram.com | Celebrity gossip reels"),
        ("irrelevant", "netflix.com | Trending TV Shows"),
        ("irrelevant", "youtube.com | Gaming livestream"),
    ]),
    ("SCROLL INSTAGRAM FOR FUN", [
        ("relevant", "instagram.com | Instagram Reels"),
        ("relevant", "instagram.com | Explore trending reels and posts"),
        ("relevant", "instagram.com | Funny memes and entertainment"),
        ("irrelevant", "code | assignment.py - Visual Studio Code"),
        ("irrelevant", "coursera.org | Machine Learning Course"),
        ("irrelevant", "github.com | Python project repository"),
        ("irrelevant", "stackoverflow.com | Debugging Python error"),
    ]),
    ("BUY A NEW LAPTOP", [
        ("relevant", "amazon.com | Laptop Computers - Latest Models"),
        ("relevant", "youtube.com | Best Laptops 2026 Buying Guide"),
        ("relevant", "reddit.com | Laptop buying recommendations"),
        ("relevant", "notebookcheck.net | Laptop Reviews and Benchmarks"),
        ("irrelevant", "instagram.com | Random reels"),
        ("irrelevant", "netflix.com | Movies and TV Shows"),
        ("irrelevant", "youtube.com | Celebrity gossip"),
    ]),
    ("BUILD A MINECRAFT IRON FARM", [
        ("relevant", "youtube.com | Minecraft Iron Farm Tutorial"),
        ("relevant", "minecraft.wiki | Iron Golem Farming Guide"),
        ("relevant", "reddit.com | Minecraft Iron Farm Design"),
        ("relevant", "youtube.com | Minecraft Survival Iron Farm Build"),
        ("irrelevant", "reddit.com | Celebrity drama discussion"),
        ("irrelevant", "instagram.com | Random reels"),
        ("irrelevant", "netflix.com | Horror Movies"),
    ]),
    ("FIND A GOOD RAMEN RECIPE", [
        ("relevant", "youtube.com | Best Ramen Recipe - Easy Homemade Ramen"),
        ("relevant", "reddit.com | Homemade ramen recipe recommendations"),
        ("relevant", "allrecipes.com | Japanese Ramen Recipe"),
        ("relevant", "google.com | Easy spicy ramen recipe"),
        ("irrelevant", "youtube.com | MrBeast challenge"),
        ("irrelevant", "instagram.com | Fashion reels"),
        ("irrelevant", "netflix.com | New movies"),
    ]),
]

def main():
    embedder = MiniLMEmbedder()
    alignment = AlignmentEngine()

    print("LOCKEDIN alignment benchmark")
    print("=" * 135)

    for goal, activities in CASES:
        print(f"\nGOAL: {goal}")
        print("-" * 135)

        goal_embedding = embedder.embed(goal)
        results = []

        for label, activity in activities:
            activity_embedding = embedder.embed(activity)

            result = alignment.compare(
                goal,
                activity,
                goal_embedding,
                activity_embedding,
            )

            results.append((result, label, activity))

        results.sort(
            key=lambda item: item[0].combined_score,
            reverse=True,
        )

        print(
            f"{'SEM':>7} | "
            f"{'LEX':>7} | "
            f"{'SCORE':>7} | "
            f"{'EXPECTED':>10} | "
            f"{'MODEL':>10} | "
            f"{'MATCHED TERMS':<30} | ACTIVITY"
        )
        print("-" * 135)

        for result, expected, activity in results:
            terms = ", ".join(result.matched_terms)

            print(
                f"{result.semantic_similarity:>7.4f} | "
                f"{result.lexical_overlap:>7.4f} | "
                f"{result.combined_score:>7.4f} | "
                f"{expected:>10} | "
                f"{result.decision:>10} | "
                f"{terms:<30} | "
                f"{activity}"
            )

if __name__ == "__main__":
    main()