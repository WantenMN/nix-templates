{
  pkgs ? import <nixpkgs> {
    config.allowUnfree = true;
  },
}:

pkgs.mkShell rec {
  name = "speech-recognition";
  buildInputs = with pkgs; [
    (pkgs.python3.withPackages (
      python-pkgs: with python-pkgs; [
        keyboard
        requests
        pyperclip
      ]
    ))
  ];

  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath buildInputs;
}
