from geoml_env import GeoMLEnv

def main():
    print("GeoML-RescueEnv server initialized.")
    env = GeoMLEnv()
    # In a real cloud run, OpenEnv binds to this entry point to expose the API.
    return env

if __name__ == "__main__":
    main()