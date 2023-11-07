from compile import check_dependencies, get_vcpkg_root, setup_and_install_vcpkgs


def main():
    check_dependencies()

    vcpkg_folder = get_vcpkg_root()

    setup_and_install_vcpkgs(vcpkg_folder)


if __name__ == '__main__':
    main()
