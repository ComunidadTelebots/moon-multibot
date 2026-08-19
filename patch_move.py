with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

parts = content.split("# === ROUTER PATCH ===")
if len(parts) == 2:
    main_body = parts[0]
    router_patch = "# === ROUTER PATCH ===" + parts[1]
    
    # Insert router_patch right before the ping route that I inserted earlier
    # or before `if __name__ == "__main__":`
    
    insertion_point = '@app.route("/api/admin/telegram_ping", methods=["GET"])'
    
    if insertion_point in main_body:
        new_content = main_body.replace(insertion_point, router_patch + "\n\n" + insertion_point)
        with open("moon_multibot.py", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Patched successfully")
    else:
        print("Insertion point not found")
else:
    print("ROUTER PATCH section not found exactly once")
