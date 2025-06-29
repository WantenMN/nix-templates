{
  description = "Flutter Template";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            android_sdk.accept_license = true;
            allowUnfree = true;
          };
        };
        nativeBuildInputs = [
        ];

        buildInputs = [
          androidSdk
          pkgs.flutter
          pkgs.jdk17
        ];

        # Android config
        buildToolsVersion = "34.0.0";
        androidComposition = pkgs.androidenv.composeAndroidPackages {
          buildToolsVersions = [
            buildToolsVersion
            "28.0.3"
          ];
          platformVersions = [
            "35"
            "28"
          ];
          includeNDK = true;
          ndkVersion = "26.3.11579264";
          cmakeVersions = [ "3.22.1" ];

          # abiVersions = [
          #   "armeabi-v7a"
          #   "arm64-v8a"
          # ];
        };
        androidSdk = androidComposition.androidsdk;
      in
      {
        devShells.default = pkgs.mkShell rec {
          inherit nativeBuildInputs buildInputs;
          ANDROID_SDK_ROOT = "${androidSdk}/libexec/android-sdk";
          GRADLE_OPTS = "-Dorg.gradle.project.android.aapt2FromMavenOverride=${ANDROID_SDK_ROOT}/build-tools/${buildToolsVersion}/aapt2";

        };
      }
    );
}
