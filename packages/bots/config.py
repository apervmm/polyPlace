CANVAS_W = 540
CANVAS_H = 540

RATE_LIMIT_PIXELS = 1000
RATE_LIMIT_WINDOW_SEC = 1  # 5 seconds

# The 8 colors supported by the canvas (must match the client palette)
PALETTE = [
    "#ff0000",  # red
    "#0000ff",  # blue
    "#008000",  # green
    "#ffff00",  # yellow
    "#000000",  # black
    "#ffffff",  # white
    "#800080",  # purple
    "#ffa500",  # orange
]

# Add or remove bots here. Drop the matching PNG into images/ before starting.
BOTS = [
    # {
    #     "name": "MonaLisa",
    #     "username": "bot_monalisa",
    #     "password": "bot_monalisa_secret",
    #     "email": "bot_monalisa@bots.internal",
    #     "image": "images/mona_lisa.png",
    # },
    {
        "name": "Apple",
        "username": "bot_apple",
        "password": "bot_apple_secret",
        "email": "bot_apple@bots.internal",
        "image": "images/apple.png",
    },
]
