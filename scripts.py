import app.dbconnect as db
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("serviceaccount.json")
firebase_admin.initialize_app(cred)

table = db.initialize_connection()

def clear_table():
    response = table.scan()
    data = response['Items']

    for item in data:
        print('Deleting item with uid:', item['uid'])
        table.delete_item(
            Key={
                'uid': item['uid']
            }
        )
    print("All items deleted successfully.")

def clear_firebase():
    users = auth.list_users().users
    for user in users:
        print('Deleting user with uid:', user.uid)
        auth.delete_user(user.uid)
    print("All users deleted successfully.")

def show_table():
    response = table.scan()
    data = response['Items']

    if not data:
        print("No items found in the table.")
    else:
        for item in data:
            print(item)

def show_firebase():
    users = auth.list_users().users
    if not users:
        print("No users found in Firebase.")
    else:
        for user in users:
            print(user, user.uid)


def show_db_and_firebase():
    print("DynamoDB Items:")
    show_table()
    print("\nFirebase Users:")
    show_firebase()

def clear_db_and_firebase():
    clear_firebase()
    clear_table()

if __name__ == "__main__":
    z = input("Do you want to clear the database and Firebase? (y/n): ")
    if z.lower() == 'y':
        clear_db_and_firebase()
    else:
        print("No action taken.")
    z = input("Do you want to show the database and Firebase? (y/n): ")
    if z.lower() == 'y':
        show_db_and_firebase()
    else:
        print("No action taken.")

