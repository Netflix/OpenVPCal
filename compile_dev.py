"""
Copyright 2024 Netflix Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from compile import check_dependencies, get_vcpkg_root, setup_and_install_vcpkgs


def main():
    check_dependencies()

    vcpkg_folder = get_vcpkg_root()

    setup_and_install_vcpkgs(vcpkg_folder)


if __name__ == '__main__':
    main()
