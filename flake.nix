{
  description = "Kilo Code Marketplace development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs, ... }:
    let
      systems = [
        "aarch64-darwin"
        "x86_64-linux"
      ];

      forAllSystems = nixpkgs.lib.genAttrs systems;

      mkDevShell =
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
        in
        pkgs.mkShell {
          name = "kilo-code-marketplace";

          packages = with pkgs; [
            git
            git-lfs
            nodejs_24
            corepack_24
          ];

          env = {
            # Node.js TLS: extra CA certificates for the wrangler Node.js process.
            # Use the Nix-managed CA bundle so this works on both Linux and macOS.
            NODE_EXTRA_CA_CERTS = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
          };

          shellHook = ''
            # workerd's BoringSSL calls SSL_CTX_set_default_verify_paths(), which reads
            # SSL_CERT_FILE and falls back to the compiled-in /etc/ssl/cert.pem.
            # NixOS doesn't create /etc/ssl/cert.pem, so force-export SSL_CERT_FILE here.
            # We use shellHook (not env) because nixpkgs stdenv also sets SSL_CERT_FILE
            # internally, which silently wins over the env attribute.
            # Guard to Linux only: macOS ships its own trust store and the hard-coded
            # /etc/ssl/certs/ca-certificates.crt path does not exist there.
            ${pkgs.lib.optionalString pkgs.stdenv.isLinux ''
              export SSL_CERT_FILE="${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
            ''}
          '';
        };
    in
    {
      devShells = forAllSystems (system: {
        default = mkDevShell system;
      });
    };
}
