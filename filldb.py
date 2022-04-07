from db.models import *


def create_users():
    for i in range(10):
        Person.create(
            name=f'user{i}',
            real_name=f'User {i}'
        )


def create_artist():
    for i in range(3):
        Artist.create(
            person=i+1,
            description='Test info for User {i}. This text can be useful for user who see it'
        )


def main():
    create_tables()
    create_users()
    create_artist()


if __name__ == '__main__':
    main()
