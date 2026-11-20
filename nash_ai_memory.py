"""Nash.AI project memory/configuration.

This is a Python version of the project's memory file.
Run `python nash_ai_memory.py` to print the project summary or import
NASH_AI_PROJECT from another Python program.
"""

NASH_AI_PROJECT = {
    "name": "Nash.AI",
    "description": "AI business-management assistant for small businesses.",
    "mission": "Help business owners understand records, prepare quotations, track orders and follow up on pending work.",
    "target_users": ["small businesses", "wholesalers", "distributors", "manufacturers"],
    "core_features": [
        "business dashboard",
        "customer records",
        "product and stock records",
        "order tracking and due-date reminders",
        "quotation generation",
        "income and expense records",
        "AI question answering over business records",
        "CSV import and export"
    ],
    "preferred_stack": {
        "spreadsheet_prototype": "Google Sheets",
        "visual_no_code_prototype": "Glide",
        "database_backend": "Supabase",
        "programming_language": "Python",
        "ai_layer": "OpenAI API",
        "current_mvp_database": "SQLite"
    },
    "principles": [
        "Start with a narrow, useful MVP.",
        "Do not claim to replace TallyPrime.",
        "Use customer permission before handling real business data.",
        "Use fictional data for early testing.",
        "Require human review for quotations and business decisions.",
        "Protect API keys and customer information."
    ],
    "development_status": {
        "local_streamlit_mvp": "starter implementation",
        "supabase_sync": "not implemented",
        "google_sheets_live_sync": "not implemented",
        "whatsapp_reminders": "not implemented",
        "multi_user_authentication": "not implemented",
        "production_deployment": "not implemented"
    }
}


if __name__ == "__main__":
    import json
    print(json.dumps(NASH_AI_PROJECT, indent=2, ensure_ascii=False))
