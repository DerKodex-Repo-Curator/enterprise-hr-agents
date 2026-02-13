import google.adk
print(f"google.adk: {dir(google.adk)}")

try:
    import google.adk.server
    print(f"google.adk.server: {dir(google.adk.server)}")
except ImportError:
    pass




