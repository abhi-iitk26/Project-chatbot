"""
RAG Evaluation System Readiness Check
=====================================

This script checks if your evaluation system is ready to run.
"""


def check_imports():
    """Check if all required imports are available"""
    print("🔍 Checking Required Imports...")

    issues = []

    # Basic Python libraries
    try:
        import os
        import json
        import time
        from datetime import datetime
        from typing import Dict, List, Any, Optional
        from dataclasses import dataclass

        print("✅ Basic Python libraries: OK")
    except ImportError as e:
        issues.append(f"❌ Basic libraries: {e}")

    # Data science libraries
    try:
        import pandas as pd
        import numpy as np

        print("✅ Data science libraries (pandas, numpy): OK")
    except ImportError as e:
        issues.append(f"❌ Data science libraries: {e}")

    # Machine learning libraries
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        from sentence_transformers import SentenceTransformer

        print("✅ ML libraries (sklearn, sentence-transformers): OK")
    except ImportError as e:
        issues.append(f"❌ ML libraries: {e}")

    # Visualization libraries
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        print("✅ Visualization libraries (matplotlib, seaborn): OK")
    except ImportError as e:
        issues.append(f"❌ Visualization libraries: {e}")

    # Your chatbot
    try:
        from core_chatbot import TextileChatbot

        print("✅ TextileChatbot import: OK")
    except ImportError as e:
        issues.append(f"❌ TextileChatbot import: {e}")

    return issues


def check_data_files():
    """Check if JSON data files are available"""
    print("\n📁 Checking Data Files...")

    required_files = [
        "structured_bom_data_final.json",
        "rag_ready_coating.json",
        "rag_ready_processing.json",
        "rag_ready_sectional_warping_complete.json",
        "all_quality_chunks.json",
    ]

    available_files = []
    missing_files = []

    for file in required_files:
        if os.path.exists(file):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        available_files.append(f"✅ {file}: {len(data)} items")
                    else:
                        missing_files.append(f"⚠️  {file}: Empty or invalid format")
            except Exception as e:
                missing_files.append(f"❌ {file}: Error reading - {e}")
        else:
            missing_files.append(f"❌ {file}: File not found")

    for file_status in available_files:
        print(file_status)

    for file_status in missing_files:
        print(file_status)

    return len(missing_files) == 0


def check_evaluation_system():
    """Check if evaluation system components work"""
    print("\n🧪 Checking Evaluation System...")

    try:
        # Try to import the evaluation system
        from evaluation_system import create_test_dataset, RAGEvaluator

        print("✅ Evaluation system import: OK")

        # Try to create test dataset
        test_queries = create_test_dataset()
        print(f"✅ Test dataset creation: OK ({len(test_queries)} queries)")

        # Check query structure
        sample_query = test_queries[0]
        required_fields = ["query", "ground_truth", "category"]

        for field in required_fields:
            if field in sample_query:
                print(f"✅ Query field '{field}': OK")
            else:
                print(f"❌ Query field '{field}': Missing")

        return True

    except Exception as e:
        print(f"❌ Evaluation system: {e}")
        return False


def check_chatbot_readiness():
    """Check if the chatbot can be initialized"""
    print("\n🤖 Checking Chatbot Readiness...")

    try:
        from core_chatbot import TextileChatbot

        # Try to create chatbot instance
        chatbot = TextileChatbot()
        print("✅ Chatbot initialization: OK")

        # Try a simple query
        test_response = chatbot.process("What is GSM?")
        if test_response and len(test_response) > 10:
            print("✅ Chatbot response generation: OK")
            print(f"   Sample response: {test_response[:60]}...")
            return True
        else:
            print("⚠️  Chatbot response: Very short or empty")
            return False

    except Exception as e:
        print(f"❌ Chatbot: {e}")
        return False


def main():
    """Main readiness check"""
    print("🚀 RAG Evaluation System Readiness Check")
    print("=" * 50)

    # Check imports
    import_issues = check_imports()

    # Check data files
    data_files_ok = check_data_files()

    # Check evaluation system
    eval_system_ok = check_evaluation_system()

    # Check chatbot
    chatbot_ok = check_chatbot_readiness()

    # Summary
    print("\n" + "=" * 50)
    print("READINESS SUMMARY")
    print("=" * 50)

    if len(import_issues) == 0:
        print("✅ All required libraries are installed")
    else:
        print("❌ Missing libraries:")
        for issue in import_issues:
            print(f"   {issue}")

    if data_files_ok:
        print("✅ Data files are available")
    else:
        print(
            "⚠️  Some data files are missing (evaluation will use manual queries only)"
        )

    if eval_system_ok:
        print("✅ Evaluation system is working")
    else:
        print("❌ Evaluation system has issues")

    if chatbot_ok:
        print("✅ Chatbot is ready")
    else:
        print("❌ Chatbot has issues")

    # Overall readiness
    if len(import_issues) == 0 and eval_system_ok and chatbot_ok:
        print("\n🎉 SYSTEM IS READY FOR EVALUATION!")
        print("\nNext steps:")
        print("1. Run: python evaluation_system.py")
        print("2. Or run: python simple_evaluation.py")
    else:
        print("\n⚠️  SYSTEM NEEDS ATTENTION")
        print("\nTo fix issues:")
        if len(import_issues) > 0:
            print("1. Install missing libraries: pip install -r requirements.txt")
        if not chatbot_ok:
            print("2. Check your chatbot configuration")
        if not eval_system_ok:
            print("3. Check evaluation_system.py for errors")


if __name__ == "__main__":
    import os
    import json

    main()
