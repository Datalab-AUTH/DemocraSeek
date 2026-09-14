/** App-wide footer with partner marks and legal copy. */

import { branding } from "../branding";
import { formatUi, useUi } from "../i18n";

/** Placeholder until a Terms & Services page is published. */
export const TERMS_HREF = "https://innovade-democracy.eu/privacy-policy";

/** Set `href` to an external URL to make a logo clickable, or `null` for no link. */
const FOOTER_LOGOS = [
  {
    src: "/logo_innovade_full.svg",
    href: "https://innovade-democracy.eu/" as string | null,
    altKey: "innovadeLogoAlt" as const,
  },
  {
    src: "/eu_funded_en.svg",
    href: null as string | null,
    altKey: "euLogoAlt" as const,
  },
];

function FooterLogo({
  src,
  alt,
  href,
}: {
  src: string;
  alt: string;
  href: string | null;
}): JSX.Element {
  const image = <img className="app-footer__logo" src={src} alt={alt} />;
  if (!href) return image;
  return (
    <a
      className="app-footer__logo-link"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
    >
      {image}
    </a>
  );
}

export function Footer(): JSX.Element {
  const { ui } = useUi();
  const year = new Date().getFullYear();

  return (
    <footer className="app-footer">
      <div className="app-footer__inner">
        <div className="app-footer__logos" aria-label={ui.footer.logosLabel}>
          {FOOTER_LOGOS.map((logo) => (
            <FooterLogo
              key={logo.src}
              src={logo.src}
              alt={ui.footer[logo.altKey]}
              href={logo.href}
            />
          ))}
        </div>

        <div className="app-footer__legal">
          <p className="app-footer__copyright">
            {formatUi(ui.footer.copyright, { year, appName: branding.appName })}
          </p>
          <p className="app-footer__made-by">
            {formatUi(ui.footer.madeBy, { project: branding.projectName })}
          </p>
          <a className="app-footer__terms" href={TERMS_HREF}>
            {ui.footer.terms}
          </a>
        </div>
      </div>
    </footer>
  );
}
