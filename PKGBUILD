# Maintainer: 10supernova <https://github.com/10supernova>
pkgname=mk1300-linux
pkgver=1.0.0
pkgrel=1
pkgdesc="Native Linux per-key RGB lighting controller for Ant Esports MK1300 V2 keyboard"
arch=('any')
url="https://github.com/10supernova/mk1300-linux"
license=('Apache-2.0')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'python-hidapi')
optdepends=(
    'ttf-jetbrains-mono-nerd: Best typography for key legends'
)
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/10supernova/${pkgname}/archive/refs/tags/v${pkgver}.tar.gz")
sha256sums=('SKIP')

package() {
    cd "${srcdir}/${pkgname}-${pkgver}"

    # Install python module
    local python_version=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    install -d "${pkgdir}/usr/lib/python${python_version}/site-packages/mk1300"
    cp -r mk1300/* "${pkgdir}/usr/lib/python${python_version}/site-packages/mk1300/"

    # Install binaries
    install -d "${pkgdir}/usr/bin"
    install -m755 mk1300-cli "${pkgdir}/usr/bin/mk1300-cli"
    install -m755 mk1300-gui "${pkgdir}/usr/bin/mk1300-gui"

    # Install udev rules
    install -d "${pkgdir}/usr/lib/udev/rules.d"
    install -m644 udev/99-mk1300.rules "${pkgdir}/usr/lib/udev/rules.d/99-mk1300.rules"

    # Install desktop entry
    install -d "${pkgdir}/usr/share/applications"
    install -m644 io.github.antrgb.MK1300Linux.desktop "${pkgdir}/usr/share/applications/io.github.antrgb.MK1300Linux.desktop"

    # Install icons
    install -d "${pkgdir}/usr/share/icons/hicolor/scalable/apps"
    install -m644 resources/io.github.antrgb.MK1300Linux.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/io.github.antrgb.MK1300Linux.svg"

    # Install systemd user service
    install -d "${pkgdir}/usr/lib/systemd/user"
    install -m644 systemd/mk1300-restore.service "${pkgdir}/usr/lib/systemd/user/mk1300-restore.service"

    # Install licenses and notice
    install -d "${pkgdir}/usr/share/licenses/${pkgname}"
    install -m644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
    install -m644 NOTICE "${pkgdir}/usr/share/licenses/${pkgname}/NOTICE"
}
