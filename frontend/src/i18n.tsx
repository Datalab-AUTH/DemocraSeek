/** Application-interface translations. Onboarding policy wording stays backend-driven. */

import { createContext, useContext, useEffect, type ReactNode } from "react";

export type UiLocale = "en" | "el" | "fr" | "es" | "nl-BE";

export interface UiCopy {
  language: { label: string };
  theme: { group: string; light: string; system: string; dark: string; suffix: string };
  welcome: {
    eyebrow: string;
    title: string;
    lead: string;
    start: string;
    aboutLabel: string;
    aboutTitle: string;
    aboutText: string;
  };
  app: { configError: string; loading: string };
  header: {
    newConversation: string;
    preferences: string;
    tailoredDialog: string;
    tailoredTitle: string;
    role: string;
    intent: string;
    support: string;
    mode: string;
    note: string;
    update: string;
    startOver: string;
    privacy: string;
  };
  chat: {
    conversation: string;
    you: string;
    finding: string;
    questionLabel: string;
    placeholder: string;
    working: string;
    ask: string;
    error: string;
  };
  empty: {
    eyebrow: string;
    title: string;
    lead: string;
    libraryNotReady: string;
    pendingMaterial: string;
    examplesTitle: string;
    /** What the answers are based on, shown under the starter questions. */
    scope: string;
  };
  answer: {
    copied: string;
    copy: string;
    unconfirmedTitle: string;
    unavailableTitle: string;
    insufficientTitle: string;
    unconfirmedBody: string;
    retryDifferent: string;
    retryLater: string;
    insufficientHint: string;
    openSource: string;
    sourcesLabel: string;
    sourcesTitle: string;
    sourcesSummary: string;
    viewSource: string;
    page: string;
    exactQuote: string;
    fromImage: string;
    sourceExcerpt: string;
    image: string;
    externalSource: string;
  };
  figures: {
    label: string;
    figureFrom: string;
    fromDocument: string;
    multiple: string;
    derived: string;
  };
  source: {
    dialog: string;
    sourcePosition: string;
    answerSource: string;
    pager: string;
    previous: string;
    next: string;
    close: string;
    source: string;
    metadata: string;
    page: string;
    pageLabel: string;
    pageOf: string;
    views: string;
    excerptTab: string;
    fullPageTab: string;
    whyShown: string;
    excerptHeading: string;
    seeOnPage: string;
    figureSection: string;
    imageFromPage: string;
    imageOnPage: string;
    loadingDetails: string;
    textFromSource: string;
    highlighted: string;
    loadingText: string;
    imageNoText: string;
    noReadableText: string;
    truncated: string;
    back: string;
    openOriginalImage: string;
    openOriginalPdf: string;
    loadingOriginal: string;
    exactBadge: string;
    exactTitle: string;
    exactDetail: string;
    figureBadge: string;
    figureTitle: string;
    figureDetail: string;
    passageBadge: string;
    passageTitle: string;
    passageDetail: string;
    loadError: string;
    externalBadge: string;
    externalAboutTitle: string;
    externalAboutText: string;
    authorsLabel: string;
    publishersLabel: string;
    publishedLabel: string;
    visitExternal: string;
  };
  footer: {
    logosLabel: string;
    innovadeLogoAlt: string;
    euLogoAlt: string;
    copyright: string;
    madeBy: string;
    terms: string;
  };
}

const EN: UiCopy = {
  language: { label: "Choose your language" },
  theme: { group: "Colour theme", light: "Light", system: "System", dark: "Dark", suffix: "theme" },
  welcome: {
    eyebrow: "INNOVADE knowledge, made easier to explore",
    title: "Explore digital democracy with evidence you can check.",
    lead: "DemocraSeek helps you ask questions about digital democracy and receive clear, source-grounded answers adapted to what you need.",
    start: "Start your conversation",
    aboutLabel: "About INNOVADE",
    aboutTitle: "About INNOVADE",
    aboutText: "INNOVADE examines digital democracy and how digital participation can become more inclusive, trustworthy and useful for citizens, communities and institutions.",
  },
  app: { configError: "DemocraSeek cannot start without its onboarding configuration.", loading: "Loading DemocraSeek…" },
  header: {
    newConversation: "New conversation", preferences: "Answer preferences",
    tailoredDialog: "How answers are tailored", tailoredTitle: "How answers are tailored",
    role: "You are asking as", intent: "You want to", support: "What supports you", mode: "Answer style",
    note: "These choices only change how the answer is explained.", update: "Update preferences",
    startOver: "Start over", privacy: "Saved only in this browser.",
  },
  chat: {
    conversation: "Conversation", you: "You", finding: "Finding the most helpful information…",
    questionLabel: "Your question", placeholder: "Ask a question about digital democracy…",
    working: "Working…", ask: "Ask", error: "We could not send your question. Please try again.",
  },
  empty: {
    eyebrow: "Ask in your own words", title: "What would you like to know?",
    lead: "Ask about {project} or choose a question below. Each answer lets you open the source and check where the information came from.",
    libraryNotReady: "The information library is not ready yet. Please contact the person managing DemocraSeek.",
    pendingMaterial: "Some new material is still being prepared and is not available in answers yet.",
    examplesTitle: "Not sure where to start?",
    scope: "DemocraSeek answers only from the documents in the {project} knowledge base: project deliverables and selected publications. It does not search the internet and does not use general knowledge. If the documents do not cover a question, it says so.",
  },
  answer: {
    copied: "Copied", copy: "Copy answer", unconfirmedTitle: "We could not confirm this answer",
    unavailableTitle: "Answers are temporarily unavailable", insufficientTitle: "We could not find enough information",
    unconfirmedBody: "We found relevant information, but could not confirm that the answer matched its sources, so we did not show it.",
    retryDifferent: "Try asking the same thing in a slightly different way.", retryLater: "Please wait a moment and try again.",
    insufficientHint: "The available documents do not support a reliable answer, so DemocraSeek will not guess. Try rephrasing the question or ask about a different topic.",
    openSource: "Open source {id}: {document}, page {page}", sourcesLabel: "Sources for this answer",
    sourcesTitle: "Check the sources", sourcesSummary: "Open a source to see where the answer came from",
    viewSource: "View source details {id}: {document}, page {page}", page: "Page {page}",
    exactQuote: "Exact quote", fromImage: "From an image", sourceExcerpt: "Source excerpt", image: "image",
    externalSource: "External source",
  },
  figures: {
    label: "Figures from the cited source", figureFrom: "Figure from {document}, page {page}",
    fromDocument: "From {document}, page {page}", multiple: "{count} figures from the cited pages",
    derived: "This answer uses information read from this image. Open it to check the details yourself.",
  },
  source: {
    dialog: "Source {id}: {document}, page {page}", sourcePosition: "Source {current} of {total}",
    answerSource: "Answer source", pager: "Move between answer sources", previous: "Previous source",
    next: "Next source", close: "Close source panel", source: "Source", metadata: "Source metadata",
    page: "Page {page}", pageLabel: "Cited page", pageOf: "Page {page} of {total}", views: "Source views",
    excerptTab: "Source excerpt", fullPageTab: "Full page", whyShown: "Why this source is shown",
    excerptHeading: "Source excerpt", seeOnPage: "See this excerpt on the full page",
    figureSection: "Figure on the cited page", imageFromPage: "Image from this page",
    imageOnPage: "Image on page {page}", loadingDetails: "Loading source details…",
    textFromSource: "Text from the source", highlighted: "Excerpt highlighted",
    loadingText: "Loading page text…", imageNoText: "This source is an image and does not have a separate text page.",
    noReadableText: "No readable text was extracted from this page. It may be a scan or a full-page image.",
    truncated: "Only the beginning of this long page is shown. Open the original PDF to read the rest.",
    back: "Back to answer", openOriginalImage: "Open the original image", openOriginalPdf: "Open the original PDF",
    loadingOriginal: "Loading original…", exactBadge: "Exact match", exactTitle: "This text appears on the page",
    exactDetail: "We found the same wording in the original source.", figureBadge: "From an image",
    figureTitle: "This answer uses an image", figureDetail: "The image was read when the document was added. Open it below to check the details.",
    passageBadge: "From the source", passageTitle: "Taken from this page",
    passageDetail: "This excerpt comes directly from the original source.", loadError: "We could not load the source details.",
    externalBadge: "External source", externalAboutTitle: "About this publication",
    externalAboutText: "This publication was used to prepare the answer. To respect copyright, we do not display excerpts from external publications. You can read the full text on the publisher's website.",
    authorsLabel: "Authors", publishersLabel: "Publisher", publishedLabel: "Publication date",
    visitExternal: "Visit original source",
  },
  footer: {
    logosLabel: "Partner logos",
    innovadeLogoAlt: "INNOVADE",
    euLogoAlt: "Funded by the European Union",
    copyright: "© {year} {appName}",
    madeBy: "Made by DATALAB for {project}",
    terms: "Privacy Policy",
  },
};

const EL: UiCopy = {
  language: { label: "Επιλέξτε γλώσσα" },
  theme: { group: "Θέμα εμφάνισης", light: "Φωτεινό", system: "Συστήματος", dark: "Σκούρο", suffix: "θέμα" },
  welcome: {
    eyebrow: "Η γνώση του INNOVADE, πιο εύκολη στην εξερεύνηση",
    title: "Εξερευνήστε την ψηφιακή δημοκρατία με τεκμήρια που μπορείτε να ελέγξετε.",
    lead: "Το DemocraSeek σάς βοηθά να κάνετε ερωτήσεις για την ψηφιακή δημοκρατία και να λαμβάνετε σαφείς, τεκμηριωμένες απαντήσεις προσαρμοσμένες σε ό,τι χρειάζεστε.",
    start: "Ξεκινήστε τη συζήτησή σας", aboutLabel: "Σχετικά με το INNOVADE", aboutTitle: "Σχετικά με το INNOVADE",
    aboutText: "Το INNOVADE εξετάζει την ψηφιακή δημοκρατία και πώς η ψηφιακή συμμετοχή μπορεί να γίνει πιο συμπεριληπτική, αξιόπιστη και χρήσιμη για πολίτες, κοινότητες και θεσμούς.",
  },
  app: { configError: "Το DemocraSeek δεν μπορεί να ξεκινήσει χωρίς τη ρύθμιση του onboarding.", loading: "Φόρτωση του DemocraSeek…" },
  header: {
    newConversation: "Νέα συζήτηση", preferences: "Προτιμήσεις απάντησης",
    tailoredDialog: "Πώς προσαρμόζονται οι απαντήσεις", tailoredTitle: "Πώς προσαρμόζονται οι απαντήσεις",
    role: "Ρωτάτε ως", intent: "Θέλετε να", support: "Τι σας υποστηρίζει", mode: "Μορφή απάντησης",
    note: "Αυτές οι επιλογές αλλάζουν μόνο τον τρόπο εξήγησης της απάντησης.", update: "Αλλαγή προτιμήσεων",
    startOver: "Επανεκκίνηση", privacy: "Αποθηκεύεται μόνο σε αυτόν τον browser.",
  },
  chat: {
    conversation: "Συζήτηση", you: "Εσείς", finding: "Αναζήτηση των πιο χρήσιμων πληροφοριών…",
    questionLabel: "Η ερώτησή σας", placeholder: "Κάντε μια ερώτηση για την ψηφιακή δημοκρατία…",
    working: "Επεξεργασία…", ask: "Ρώτησε", error: "Δεν ήταν δυνατή η αποστολή της ερώτησης. Δοκιμάστε ξανά.",
  },
  empty: {
    eyebrow: "Ρωτήστε με δικά σας λόγια", title: "Τι θα θέλατε να μάθετε;",
    lead: "Ρωτήστε για το {project} ή επιλέξτε μία από τις παρακάτω ερωτήσεις. Κάθε απάντηση σας επιτρέπει να ανοίξετε την πηγή και να ελέγξετε από πού προήλθε η πληροφορία.",
    libraryNotReady: "Η βιβλιοθήκη πληροφοριών δεν είναι ακόμη έτοιμη. Επικοινωνήστε με τον υπεύθυνο του DemocraSeek.",
    pendingMaterial: "Κάποιο νέο υλικό προετοιμάζεται ακόμη και δεν είναι διαθέσιμο στις απαντήσεις.",
    examplesTitle: "Δεν ξέρετε από πού να ξεκινήσετε;",
    scope: "Το DemocraSeek απαντά μόνο από τα έγγραφα της βάσης γνώσης {project}: παραδοτέα του έργου και επιλεγμένες δημοσιεύσεις. Δεν αναζητά στο διαδίκτυο και δεν χρησιμοποιεί γενική γνώση. Αν τα έγγραφα δεν καλύπτουν μια ερώτηση, το αναφέρει.",
  },
  answer: {
    copied: "Αντιγράφηκε", copy: "Αντιγραφή απάντησης", unconfirmedTitle: "Δεν μπορέσαμε να επιβεβαιώσουμε αυτή την απάντηση",
    unavailableTitle: "Οι απαντήσεις είναι προσωρινά μη διαθέσιμες", insufficientTitle: "Δεν βρέθηκαν αρκετές πληροφορίες",
    unconfirmedBody: "Βρήκαμε σχετικές πληροφορίες, αλλά δεν μπορέσαμε να επιβεβαιώσουμε ότι η απάντηση συμφωνούσε με τις πηγές της, γι’ αυτό δεν την εμφανίσαμε.",
    retryDifferent: "Δοκιμάστε να ρωτήσετε το ίδιο με λίγο διαφορετικό τρόπο.", retryLater: "Περιμένετε λίγο και δοκιμάστε ξανά.",
    insufficientHint: "Τα διαθέσιμα έγγραφα δεν υποστηρίζουν μια αξιόπιστη απάντηση, επομένως το DemocraSeek δεν θα μαντέψει. Διατυπώστε διαφορετικά την ερώτηση ή ρωτήστε για άλλο θέμα.",
    openSource: "Άνοιγμα πηγής {id}: {document}, σελίδα {page}", sourcesLabel: "Πηγές αυτής της απάντησης",
    sourcesTitle: "Ελέγξτε τις πηγές", sourcesSummary: "Ανοίξτε μια πηγή για να δείτε από πού προήλθε η απάντηση",
    viewSource: "Προβολή στοιχείων πηγής {id}: {document}, σελίδα {page}", page: "Σελίδα {page}",
    exactQuote: "Ακριβές απόσπασμα", fromImage: "Από εικόνα", sourceExcerpt: "Απόσπασμα πηγής", image: "εικόνα",
    externalSource: "Εξωτερική πηγή",
  },
  figures: {
    label: "Εικόνες από την αναφερόμενη πηγή", figureFrom: "Εικόνα από {document}, σελίδα {page}",
    fromDocument: "Από {document}, σελίδα {page}", multiple: "{count} εικόνες από τις αναφερόμενες σελίδες",
    derived: "Η απάντηση χρησιμοποιεί πληροφορίες που διαβάστηκαν από αυτή την εικόνα. Ανοίξτε την για να ελέγξετε τις λεπτομέρειες.",
  },
  source: {
    dialog: "Πηγή {id}: {document}, σελίδα {page}", sourcePosition: "Πηγή {current} από {total}",
    answerSource: "Πηγή απάντησης", pager: "Μετακίνηση μεταξύ πηγών", previous: "Προηγούμενη πηγή",
    next: "Επόμενη πηγή", close: "Κλείσιμο πηγής", source: "Πηγή", metadata: "Στοιχεία πηγής",
    page: "Σελίδα {page}", pageLabel: "Σελίδα παραπομπής", pageOf: "Σελίδα {page} από {total}", views: "Προβολές πηγής",
    excerptTab: "Απόσπασμα πηγής", fullPageTab: "Πλήρης σελίδα", whyShown: "Γιατί εμφανίζεται αυτή η πηγή",
    excerptHeading: "Απόσπασμα πηγής", seeOnPage: "Δείτε το απόσπασμα στην πλήρη σελίδα",
    figureSection: "Εικόνα στην αναφερόμενη σελίδα", imageFromPage: "Εικόνα από αυτή τη σελίδα",
    imageOnPage: "Εικόνα στη σελίδα {page}", loadingDetails: "Φόρτωση στοιχείων πηγής…",
    textFromSource: "Κείμενο από την πηγή", highlighted: "Το απόσπασμα επισημαίνεται",
    loadingText: "Φόρτωση κειμένου σελίδας…", imageNoText: "Αυτή η πηγή είναι εικόνα και δεν διαθέτει ξεχωριστή σελίδα κειμένου.",
    noReadableText: "Δεν εξήχθη αναγνώσιμο κείμενο από αυτή τη σελίδα. Μπορεί να είναι σάρωση ή ολοσέλιδη εικόνα.",
    truncated: "Εμφανίζεται μόνο η αρχή αυτής της μεγάλης σελίδας. Ανοίξτε το αρχικό PDF για να διαβάσετε τα υπόλοιπα.",
    back: "Πίσω στην απάντηση", openOriginalImage: "Άνοιγμα αρχικής εικόνας", openOriginalPdf: "Άνοιγμα αρχικού PDF",
    loadingOriginal: "Φόρτωση πρωτοτύπου…", exactBadge: "Ακριβής αντιστοίχιση", exactTitle: "Αυτό το κείμενο υπάρχει στη σελίδα",
    exactDetail: "Βρήκαμε την ίδια διατύπωση στην αρχική πηγή.", figureBadge: "Από εικόνα",
    figureTitle: "Η απάντηση χρησιμοποιεί εικόνα", figureDetail: "Η εικόνα αναγνώστηκε κατά την προσθήκη του εγγράφου. Ανοίξτε την παρακάτω για να ελέγξετε τις λεπτομέρειες.",
    passageBadge: "Από την πηγή", passageTitle: "Λήφθηκε από αυτή τη σελίδα",
    passageDetail: "Αυτό το απόσπασμα προέρχεται απευθείας από την αρχική πηγή.", loadError: "Δεν ήταν δυνατή η φόρτωση των στοιχείων της πηγής.",
    externalBadge: "Εξωτερική πηγή", externalAboutTitle: "Σχετικά με τη δημοσίευση",
    externalAboutText: "Αυτή η δημοσίευση χρησιμοποιήθηκε για τη διαμόρφωση της απάντησης. Για λόγους πνευματικών δικαιωμάτων, δεν εμφανίζουμε αποσπάσματα από εξωτερικές δημοσιεύσεις. Μπορείτε να διαβάσετε ολόκληρο το κείμενο στον ιστότοπο του εκδότη.",
    authorsLabel: "Συγγραφείς", publishersLabel: "Εκδότης", publishedLabel: "Ημερομηνία δημοσίευσης",
    visitExternal: "Μετάβαση στην αρχική πηγή",
  },
  footer: {
    logosLabel: "Λογότυπα συνεργατών",
    innovadeLogoAlt: "INNOVADE",
    euLogoAlt: "Χρηματοδοτείται από την Ευρωπαϊκή Ένωση",
    copyright: "© {year} {appName}",
    madeBy: "Από το DATALAB για το {project}",
    terms: "Πολιτική απορρήτου",
  },
};

const FR: UiCopy = {
  language: { label: "Choisissez votre langue" },
  theme: { group: "Thème d’affichage", light: "Clair", system: "Système", dark: "Sombre", suffix: "thème" },
  welcome: {
    eyebrow: "Les connaissances d’INNOVADE, plus faciles à explorer", title: "Explorez la démocratie numérique avec des preuves vérifiables.",
    lead: "DemocraSeek vous aide à poser des questions sur la démocratie numérique et à recevoir des réponses claires, fondées sur des sources et adaptées à vos besoins.",
    start: "Commencer votre conversation", aboutLabel: "À propos d’INNOVADE", aboutTitle: "À propos d’INNOVADE",
    aboutText: "INNOVADE étudie la démocratie numérique et la manière de rendre la participation numérique plus inclusive, fiable et utile aux citoyens, aux communautés et aux institutions.",
  },
  app: { configError: "DemocraSeek ne peut pas démarrer sans sa configuration d’onboarding.", loading: "Chargement de DemocraSeek…" },
  header: {
    newConversation: "Nouvelle conversation", preferences: "Préférences de réponse", tailoredDialog: "Comment les réponses sont adaptées",
    tailoredTitle: "Comment les réponses sont adaptées", role: "Vous posez la question en tant que", intent: "Vous souhaitez",
    support: "Le soutien choisi", mode: "Format de réponse", note: "Ces choix modifient uniquement la manière dont la réponse est expliquée.",
    update: "Modifier les préférences", startOver: "Recommencer", privacy: "Enregistré uniquement dans ce navigateur.",
  },
  chat: {
    conversation: "Conversation", you: "Vous", finding: "Recherche des informations les plus utiles…", questionLabel: "Votre question",
    placeholder: "Posez une question sur la démocratie numérique…", working: "Traitement…", ask: "Demander",
    error: "Nous n’avons pas pu envoyer votre question. Veuillez réessayer.",
  },
  empty: {
    eyebrow: "Posez votre question avec vos propres mots", title: "Que souhaitez-vous savoir ?",
    lead: "Posez une question sur {project} ou choisissez-en une ci-dessous. Chaque réponse vous permet d’ouvrir la source et de vérifier l’origine de l’information.",
    libraryNotReady: "La bibliothèque d’informations n’est pas encore prête. Contactez la personne responsable de DemocraSeek.",
    pendingMaterial: "De nouveaux contenus sont encore en préparation et ne sont pas encore disponibles dans les réponses.",
    examplesTitle: "Vous ne savez pas par où commencer ?",
    scope: "DemocraSeek répond uniquement à partir des documents de la base de connaissances {project} : livrables du projet et publications sélectionnées. Il ne fait pas de recherche sur Internet et n'utilise pas de connaissances générales. Si les documents ne couvrent pas une question, il l'indique.",
  },
  answer: {
    copied: "Copié", copy: "Copier la réponse", unconfirmedTitle: "Nous n’avons pas pu confirmer cette réponse",
    unavailableTitle: "Les réponses sont temporairement indisponibles", insufficientTitle: "Nous n’avons pas trouvé suffisamment d’informations",
    unconfirmedBody: "Nous avons trouvé des informations pertinentes, mais nous n’avons pas pu confirmer que la réponse correspondait à ses sources ; elle n’a donc pas été affichée.",
    retryDifferent: "Essayez de poser la même question d’une manière légèrement différente.", retryLater: "Patientez un instant puis réessayez.",
    insufficientHint: "Les documents disponibles ne permettent pas de fournir une réponse fiable ; DemocraSeek ne va donc pas deviner. Reformulez la question ou choisissez un autre sujet.",
    openSource: "Ouvrir la source {id} : {document}, page {page}", sourcesLabel: "Sources de cette réponse", sourcesTitle: "Vérifiez les sources",
    sourcesSummary: "Ouvrez une source pour voir d’où vient la réponse", viewSource: "Voir les détails de la source {id} : {document}, page {page}",
    page: "Page {page}", exactQuote: "Citation exacte", fromImage: "Issu d’une image", sourceExcerpt: "Extrait de la source", image: "image",
    externalSource: "Source externe",
  },
  figures: {
    label: "Figures de la source citée", figureFrom: "Figure de {document}, page {page}", fromDocument: "De {document}, page {page}",
    multiple: "{count} figures provenant des pages citées", derived: "Cette réponse utilise des informations lues dans cette image. Ouvrez-la pour vérifier vous-même les détails.",
  },
  source: {
    dialog: "Source {id} : {document}, page {page}", sourcePosition: "Source {current} sur {total}", answerSource: "Source de la réponse",
    pager: "Naviguer entre les sources", previous: "Source précédente", next: "Source suivante", close: "Fermer le panneau des sources",
    source: "Source", metadata: "Métadonnées de la source", page: "Page {page}", pageLabel: "Page citée", pageOf: "Page {page} sur {total}", views: "Vues de la source",
    excerptTab: "Extrait de la source", fullPageTab: "Page complète", whyShown: "Pourquoi cette source est affichée", excerptHeading: "Extrait de la source",
    seeOnPage: "Voir cet extrait sur la page complète", figureSection: "Figure sur la page citée", imageFromPage: "Image de cette page",
    imageOnPage: "Image à la page {page}", loadingDetails: "Chargement des détails de la source…", textFromSource: "Texte de la source",
    highlighted: "Extrait surligné", loadingText: "Chargement du texte de la page…", imageNoText: "Cette source est une image et ne comporte pas de page de texte distincte.",
    noReadableText: "Aucun texte lisible n’a été extrait de cette page. Il peut s’agir d’un scan ou d’une image pleine page.",
    truncated: "Seul le début de cette longue page est affiché. Ouvrez le PDF original pour lire la suite.", back: "Retour à la réponse",
    openOriginalImage: "Ouvrir l’image originale", openOriginalPdf: "Ouvrir le PDF original", loadingOriginal: "Chargement de l’original…",
    exactBadge: "Correspondance exacte", exactTitle: "Ce texte apparaît sur la page", exactDetail: "Nous avons retrouvé la même formulation dans la source originale.",
    figureBadge: "Issu d’une image", figureTitle: "Cette réponse utilise une image", figureDetail: "L’image a été lue lors de l’ajout du document. Ouvrez-la ci-dessous pour vérifier les détails.",
    passageBadge: "Issu de la source", passageTitle: "Extrait de cette page", passageDetail: "Cet extrait provient directement de la source originale.",
    loadError: "Nous n’avons pas pu charger les détails de la source.",
    externalBadge: "Source externe", externalAboutTitle: "À propos de cette publication",
    externalAboutText: "Cette publication a servi à élaborer la réponse. Par respect du droit d’auteur, nous n’affichons pas d’extraits de publications externes. Vous pouvez lire le texte intégral sur le site de l’éditeur.",
    authorsLabel: "Auteurs", publishersLabel: "Éditeur", publishedLabel: "Date de publication",
    visitExternal: "Consulter la source originale",
  },
  footer: {
    logosLabel: "Logos des partenaires",
    innovadeLogoAlt: "INNOVADE",
    euLogoAlt: "Financé par l’Union européenne",
    copyright: "© {year} {appName}",
    madeBy: "Réalisé par DATALAB pour {project}",
    terms: "Politique de confidentialité",
  },
};

const ES: UiCopy = {
  language: { label: "Elija su idioma" },
  theme: { group: "Tema visual", light: "Claro", system: "Sistema", dark: "Oscuro", suffix: "tema" },
  welcome: {
    eyebrow: "El conocimiento de INNOVADE, más fácil de explorar", title: "Explore la democracia digital con pruebas que puede comprobar.",
    lead: "DemocraSeek le ayuda a formular preguntas sobre democracia digital y a recibir respuestas claras, basadas en fuentes y adaptadas a sus necesidades.",
    start: "Iniciar su conversación", aboutLabel: "Acerca de INNOVADE", aboutTitle: "Acerca de INNOVADE",
    aboutText: "INNOVADE estudia la democracia digital y cómo la participación digital puede ser más inclusiva, fiable y útil para ciudadanos, comunidades e instituciones.",
  },
  app: { configError: "DemocraSeek no puede iniciarse sin la configuración del onboarding.", loading: "Cargando DemocraSeek…" },
  header: {
    newConversation: "Nueva conversación", preferences: "Preferencias de respuesta", tailoredDialog: "Cómo se adaptan las respuestas",
    tailoredTitle: "Cómo se adaptan las respuestas", role: "Pregunta como", intent: "Quiere", support: "Apoyo elegido", mode: "Formato de respuesta",
    note: "Estas opciones solo cambian la manera de explicar la respuesta.", update: "Modificar preferencias", startOver: "Empezar de nuevo",
    privacy: "Guardado únicamente en este navegador.",
  },
  chat: {
    conversation: "Conversación", you: "Usted", finding: "Buscando la información más útil…", questionLabel: "Su pregunta",
    placeholder: "Haga una pregunta sobre democracia digital…", working: "Procesando…", ask: "Preguntar",
    error: "No hemos podido enviar su pregunta. Inténtelo de nuevo.",
  },
  empty: {
    eyebrow: "Pregunte con sus propias palabras", title: "¿Qué le gustaría saber?",
    lead: "Pregunte sobre {project} o elija una pregunta de las siguientes. Cada respuesta le permite abrir la fuente y comprobar de dónde procede la información.",
    libraryNotReady: "La biblioteca de información aún no está lista. Póngase en contacto con la persona responsable de DemocraSeek.",
    pendingMaterial: "Todavía se está preparando material nuevo y aún no está disponible en las respuestas.", examplesTitle: "¿No sabe por dónde empezar?",
    scope: "DemocraSeek responde únicamente a partir de los documentos de la base de conocimiento de {project}: entregables del proyecto y publicaciones seleccionadas. No busca en internet ni utiliza conocimiento general. Si los documentos no cubren una pregunta, lo indica.",
  },
  answer: {
    copied: "Copiado", copy: "Copiar respuesta", unconfirmedTitle: "No hemos podido confirmar esta respuesta",
    unavailableTitle: "Las respuestas no están disponibles temporalmente", insufficientTitle: "No hemos encontrado suficiente información",
    unconfirmedBody: "Encontramos información pertinente, pero no pudimos confirmar que la respuesta coincidiera con sus fuentes, por lo que no la mostramos.",
    retryDifferent: "Intente formular la misma pregunta de una forma ligeramente diferente.", retryLater: "Espere un momento e inténtelo de nuevo.",
    insufficientHint: "Los documentos disponibles no permiten ofrecer una respuesta fiable, por lo que DemocraSeek no hará suposiciones. Reformule la pregunta o consulte otro tema.",
    openSource: "Abrir fuente {id}: {document}, página {page}", sourcesLabel: "Fuentes de esta respuesta", sourcesTitle: "Compruebe las fuentes",
    sourcesSummary: "Abra una fuente para ver de dónde procede la respuesta", viewSource: "Ver detalles de la fuente {id}: {document}, página {page}",
    page: "Página {page}", exactQuote: "Cita exacta", fromImage: "Procedente de una imagen", sourceExcerpt: "Extracto de la fuente", image: "imagen",
    externalSource: "Fuente externa",
  },
  figures: {
    label: "Figuras de la fuente citada", figureFrom: "Figura de {document}, página {page}", fromDocument: "De {document}, página {page}",
    multiple: "{count} figuras de las páginas citadas", derived: "Esta respuesta utiliza información leída de esta imagen. Ábrala para comprobar los detalles.",
  },
  source: {
    dialog: "Fuente {id}: {document}, página {page}", sourcePosition: "Fuente {current} de {total}", answerSource: "Fuente de la respuesta",
    pager: "Moverse entre las fuentes", previous: "Fuente anterior", next: "Fuente siguiente", close: "Cerrar panel de fuentes",
    source: "Fuente", metadata: "Metadatos de la fuente", page: "Página {page}", pageLabel: "Página citada", pageOf: "Página {page} de {total}", views: "Vistas de la fuente",
    excerptTab: "Extracto de la fuente", fullPageTab: "Página completa", whyShown: "Por qué se muestra esta fuente", excerptHeading: "Extracto de la fuente",
    seeOnPage: "Ver este extracto en la página completa", figureSection: "Figura en la página citada", imageFromPage: "Imagen de esta página",
    imageOnPage: "Imagen en la página {page}", loadingDetails: "Cargando detalles de la fuente…", textFromSource: "Texto de la fuente",
    highlighted: "Extracto resaltado", loadingText: "Cargando texto de la página…", imageNoText: "Esta fuente es una imagen y no tiene una página de texto independiente.",
    noReadableText: "No se extrajo texto legible de esta página. Puede ser un escaneo o una imagen de página completa.",
    truncated: "Solo se muestra el principio de esta página larga. Abra el PDF original para leer el resto.", back: "Volver a la respuesta",
    openOriginalImage: "Abrir imagen original", openOriginalPdf: "Abrir PDF original", loadingOriginal: "Cargando original…",
    exactBadge: "Coincidencia exacta", exactTitle: "Este texto aparece en la página", exactDetail: "Encontramos la misma redacción en la fuente original.",
    figureBadge: "Procedente de una imagen", figureTitle: "Esta respuesta utiliza una imagen", figureDetail: "La imagen se leyó al añadir el documento. Ábrala a continuación para comprobar los detalles.",
    passageBadge: "Procedente de la fuente", passageTitle: "Tomado de esta página", passageDetail: "Este extracto procede directamente de la fuente original.",
    loadError: "No hemos podido cargar los detalles de la fuente.",
    externalBadge: "Fuente externa", externalAboutTitle: "Acerca de esta publicación",
    externalAboutText: "Esta publicación se utilizó para elaborar la respuesta. Por respeto a los derechos de autor, no mostramos extractos de publicaciones externas. Puede leer el texto completo en el sitio web de la editorial.",
    authorsLabel: "Autores", publishersLabel: "Editorial", publishedLabel: "Fecha de publicación",
    visitExternal: "Visitar la fuente original",
  },
  footer: {
    logosLabel: "Logotipos de socios",
    innovadeLogoAlt: "INNOVADE",
    euLogoAlt: "Financiado por la Unión Europea",
    copyright: "© {year} {appName}",
    madeBy: "Hecho por DATALAB para {project}",
    terms: "Política de privacidad",
  },
};

const NL_BE: UiCopy = {
  language: { label: "Kies uw taal" },
  theme: { group: "Weergavethema", light: "Licht", system: "Systeem", dark: "Donker", suffix: "thema" },
  welcome: {
    eyebrow: "INNOVADE-kennis, eenvoudiger te verkennen", title: "Verken digitale democratie met bewijs dat u zelf kunt controleren.",
    lead: "DemocraSeek helpt u vragen te stellen over digitale democratie en duidelijke, brongebaseerde antwoorden te krijgen die zijn aangepast aan uw behoeften.",
    start: "Start uw gesprek", aboutLabel: "Over INNOVADE", aboutTitle: "Over INNOVADE",
    aboutText: "INNOVADE onderzoekt digitale democratie en hoe digitale participatie inclusiever, betrouwbaarder en nuttiger kan worden voor burgers, gemeenschappen en instellingen.",
  },
  app: { configError: "DemocraSeek kan niet starten zonder de onboardingconfiguratie.", loading: "DemocraSeek laden…" },
  header: {
    newConversation: "Nieuw gesprek", preferences: "Antwoordvoorkeuren", tailoredDialog: "Hoe antwoorden worden aangepast",
    tailoredTitle: "Hoe antwoorden worden aangepast", role: "U vraagt als", intent: "U wilt", support: "Gekozen ondersteuning", mode: "Antwoordstijl",
    note: "Deze keuzes veranderen alleen hoe het antwoord wordt uitgelegd.", update: "Voorkeuren aanpassen", startOver: "Opnieuw beginnen",
    privacy: "Alleen in deze browser opgeslagen.",
  },
  chat: {
    conversation: "Gesprek", you: "U", finding: "De nuttigste informatie zoeken…", questionLabel: "Uw vraag",
    placeholder: "Stel een vraag over digitale democratie…", working: "Bezig…", ask: "Vraag stellen",
    error: "We konden uw vraag niet verzenden. Probeer het opnieuw.",
  },
  empty: {
    eyebrow: "Vraag het in uw eigen woorden", title: "Wat wilt u weten?",
    lead: "Stel een vraag over {project} of kies hieronder een vraag. Bij elk antwoord kunt u de bron openen en controleren waar de informatie vandaan komt.",
    libraryNotReady: "De informatiebibliotheek is nog niet klaar. Neem contact op met de beheerder van DemocraSeek.",
    pendingMaterial: "Nieuw materiaal wordt nog voorbereid en is nog niet beschikbaar in antwoorden.", examplesTitle: "Weet u niet waar te beginnen?",
    scope: "DemocraSeek antwoordt alleen op basis van de documenten in de {project}-kennisbank: projectdeliverables en geselecteerde publicaties. Het zoekt niet op het internet en gebruikt geen algemene kennis. Als de documenten een vraag niet behandelen, zegt het dat.",
  },
  answer: {
    copied: "Gekopieerd", copy: "Antwoord kopiëren", unconfirmedTitle: "We konden dit antwoord niet bevestigen",
    unavailableTitle: "Antwoorden zijn tijdelijk niet beschikbaar", insufficientTitle: "We hebben onvoldoende informatie gevonden",
    unconfirmedBody: "We vonden relevante informatie, maar konden niet bevestigen dat het antwoord met de bronnen overeenkwam. Daarom hebben we het niet getoond.",
    retryDifferent: "Probeer dezelfde vraag iets anders te formuleren.", retryLater: "Wacht even en probeer het opnieuw.",
    insufficientHint: "De beschikbare documenten ondersteunen geen betrouwbaar antwoord, dus DemocraSeek zal niet gokken. Formuleer de vraag anders of vraag naar een ander onderwerp.",
    openSource: "Bron {id} openen: {document}, pagina {page}", sourcesLabel: "Bronnen voor dit antwoord", sourcesTitle: "Controleer de bronnen",
    sourcesSummary: "Open een bron om te zien waar het antwoord vandaan komt", viewSource: "Details van bron {id} bekijken: {document}, pagina {page}",
    page: "Pagina {page}", exactQuote: "Exact citaat", fromImage: "Uit een afbeelding", sourceExcerpt: "Bronfragment", image: "afbeelding",
    externalSource: "Externe bron",
  },
  figures: {
    label: "Figuren uit de geciteerde bron", figureFrom: "Figuur uit {document}, pagina {page}", fromDocument: "Uit {document}, pagina {page}",
    multiple: "{count} figuren uit de geciteerde pagina’s", derived: "Dit antwoord gebruikt informatie die uit deze afbeelding is gelezen. Open ze om de details zelf te controleren.",
  },
  source: {
    dialog: "Bron {id}: {document}, pagina {page}", sourcePosition: "Bron {current} van {total}", answerSource: "Bron van het antwoord",
    pager: "Tussen antwoordbronnen navigeren", previous: "Vorige bron", next: "Volgende bron", close: "Bronnenpaneel sluiten",
    source: "Bron", metadata: "Bronmetadata", page: "Pagina {page}", pageLabel: "Geciteerde pagina", pageOf: "Pagina {page} van {total}", views: "Bronweergaven",
    excerptTab: "Bronfragment", fullPageTab: "Volledige pagina", whyShown: "Waarom deze bron wordt getoond", excerptHeading: "Bronfragment",
    seeOnPage: "Bekijk dit fragment op de volledige pagina", figureSection: "Figuur op de geciteerde pagina", imageFromPage: "Afbeelding van deze pagina",
    imageOnPage: "Afbeelding op pagina {page}", loadingDetails: "Brondetails laden…", textFromSource: "Tekst uit de bron",
    highlighted: "Fragment gemarkeerd", loadingText: "Paginatekst laden…", imageNoText: "Deze bron is een afbeelding en heeft geen aparte tekstpagina.",
    noReadableText: "Er is geen leesbare tekst uit deze pagina gehaald. Het kan een scan of een paginagrote afbeelding zijn.",
    truncated: "Alleen het begin van deze lange pagina wordt getoond. Open de originele PDF om de rest te lezen.", back: "Terug naar het antwoord",
    openOriginalImage: "Originele afbeelding openen", openOriginalPdf: "Originele PDF openen", loadingOriginal: "Origineel laden…",
    exactBadge: "Exacte overeenkomst", exactTitle: "Deze tekst staat op de pagina", exactDetail: "We vonden dezelfde formulering in de oorspronkelijke bron.",
    figureBadge: "Uit een afbeelding", figureTitle: "Dit antwoord gebruikt een afbeelding", figureDetail: "De afbeelding werd gelezen toen het document werd toegevoegd. Open ze hieronder om de details te controleren.",
    passageBadge: "Uit de bron", passageTitle: "Overgenomen van deze pagina", passageDetail: "Dit fragment komt rechtstreeks uit de oorspronkelijke bron.",
    loadError: "We konden de brondetails niet laden.",
    externalBadge: "Externe bron", externalAboutTitle: "Over deze publicatie",
    externalAboutText: "Deze publicatie is gebruikt om het antwoord op te stellen. Uit respect voor het auteursrecht tonen we geen fragmenten uit externe publicaties. U kunt de volledige tekst lezen op de website van de uitgever.",
    authorsLabel: "Auteurs", publishersLabel: "Uitgever", publishedLabel: "Publicatiedatum",
    visitExternal: "Naar de oorspronkelijke bron",
  },
  footer: {
    logosLabel: "Partnerlogo’s",
    innovadeLogoAlt: "INNOVADE",
    euLogoAlt: "Gefinancierd door de Europese Unie",
    copyright: "© {year} {appName}",
    madeBy: "Gemaakt door DATALAB voor {project}",
    terms: "Privacybeleid",
  },
};

const COPY: Record<UiLocale, UiCopy> = { en: EN, el: EL, fr: FR, es: ES, "nl-BE": NL_BE };

export function normalizeUiLocale(value: string | null | undefined): UiLocale {
  return value === "el" || value === "fr" || value === "es" || value === "nl-BE" ? value : "en";
}

export function getUiCopy(locale: UiLocale): UiCopy {
  return COPY[locale];
}

export function formatUi(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (whole, key: string) =>
    Object.hasOwn(values, key) ? String(values[key]) : whole,
  );
}

const UiContext = createContext<{ locale: UiLocale; ui: UiCopy }>({ locale: "en", ui: EN });

export function UiProvider({ locale, children }: { locale: UiLocale; children: ReactNode }): JSX.Element {
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);
  return <UiContext.Provider value={{ locale, ui: COPY[locale] }}>{children}</UiContext.Provider>;
}

export function useUi(): { locale: UiLocale; ui: UiCopy } {
  return useContext(UiContext);
}
