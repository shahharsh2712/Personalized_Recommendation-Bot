from personalized_recommendations.storage.database import Database


def main():
    db = Database()
    db.close()


if __name__ == "__main__":
    main()
