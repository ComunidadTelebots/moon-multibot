with open("moon_multibot.py", "r", encoding="utf-8") as f:
    content = f.read()

bad_block = """            try:
                import queue
                import queue
        if not hasattr(bot, "router_queue"):
                    bot.router_queue = queue.Queue()
                bot.router_queue.put(update)
"""

good_block = """            try:
                import queue
                if not hasattr(bot, "router_queue"):
                    bot.router_queue = queue.Queue()
                bot.router_queue.put(update)
            except Exception as e:
                pass
"""

content = content.replace(bad_block, good_block)

# Also fix the patch_bot_instances block which I might have duplicated the import queue
bad_patch_block = """        import queue
        import queue
        if not hasattr(bot, "router_queue"):"""

good_patch_block = """        import queue
        if not hasattr(bot, "router_queue"):"""

content = content.replace(bad_patch_block, good_patch_block)

with open("moon_multibot.py", "w", encoding="utf-8") as f:
    f.write(content)
