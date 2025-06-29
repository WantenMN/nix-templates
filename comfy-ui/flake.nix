{
  description = "comfyui env";

  nixConfig = {
    extra-substituters = [ "https://nix-community.cachix.org" ];
    extra-trusted-public-keys = [
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devshell = {
      url = "github:numtide/devshell";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs =
    inputs@{
      self,
      flake-parts,
      devshell,
      nixpkgs,
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ devshell.flakeModule ];
      systems = [ "x86_64-linux" ];
      perSystem =
        { system, ... }:
        let
          pkgs = import nixpkgs {
            inherit system;
            config = {
              allowUnfree = true;
              cudaSupport = true;
            };
          };

          packages = with pkgs; [
            python312
            uv

            git
            gitRepo
            gnupg
            autoconf
            curl
            procps
            gnumake
            util-linux
            m4
            gperf
            unzip
            cudatoolkit
            linuxPackages.nvidia_x11
            libGLU
            libGL
            xorg.libXi
            xorg.libXmu
            freeglut
            xorg.libXext
            xorg.libX11
            xorg.libXv
            xorg.libXrandr
            zlib
            ncurses5
            stdenv.cc
            binutils

            libgcc.lib
          ];
        in
        {
          devshells.default = {
            env = [
              {
                name = "CUDA_PATH";
                value = "${pkgs.cudatoolkit}";
              }
              {
                name = "LD_LIBRARY_PATH";
                value = pkgs.lib.makeLibraryPath packages;
              }
              {
                name = "EXTRA_LDFLAGS";
                value = "-L/lib -L${pkgs.linuxPackages.nvidia_x11}/lib";
              }
              {
                name = "EXTRA_CCFLAGS";
                value = "-I/usr/include";
              }
            ];
            packages = packages;
            commands = [
              {
                name = "comfyui";
                help = "Run ComfyUI";
                command = ''
                  if [ ! -d ".venv" ]; then
                    ${pkgs.uv}/bin/uv venv
                    ${pkgs.uv}/bin/uv pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
                    ${pkgs.uv}/bin/uv pip install -r requirements.txt
                  fi
                  ${pkgs.uv}/bin/uv run python main.py "$@"
                '';
              }
            ];

          };
        };
    };
}
