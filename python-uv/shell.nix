{
  pkgs ? import <nixpkgs> {
    config.allowUnfree = true;
  },
}:

pkgs.mkShell rec {
  name = "asr-server";
  buildInputs = with pkgs; [
    uv
  ];

  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath buildInputs;

  shellHook = ''
    # uv sync
  '';
}
