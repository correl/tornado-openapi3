{
  description = "Description for the project";

  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{ flake-parts, poetry2nix, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" ];
      perSystem = { pkgs, system, ... }:
        let
          inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryEnv;
          appEnv = mkPoetryEnv {
            projectDir = ./.;
            preferWheels = true;
          };
        in
        {
          devShells.default = appEnv.env.overrideAttrs (old: {
            buildInputs = with pkgs; [
              poetry
            ];

						PYTHON = "${appEnv}/bin/python";
          });
        };
    };
}
