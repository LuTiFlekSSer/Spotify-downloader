import SpotifyLogin


def main():
    a = SpotifyLogin.Login()
    print(a.get_authorization_url())
    a.login_with_authorization_code(input())


if __name__ == '__main__':
    main()
