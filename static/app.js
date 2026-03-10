const elements = {
  docxFile: document.getElementById("docxFile"),
  documentType: document.getElementById("documentType"),
  formGuideText: document.getElementById("formGuideText"),
  exampleAssignmentButton: document.getElementById("exampleAssignmentButton"),
  exampleAssignmentText: document.getElementById("exampleAssignmentText"),
  topicInput: document.getElementById("topicInput"),
  thesisLabel: document.getElementById("thesisLabel"),
  thesisInput: document.getElementById("thesisInput"),
  assignmentToggle: document.getElementById("assignmentToggle"),
  assignmentWrap: document.getElementById("assignmentWrap"),
  assignmentInput: document.getElementById("assignmentInput"),
  gymLevel: document.getElementById("gymLevel"),
  model: document.getElementById("model"),
  healthButton: document.getElementById("healthButton"),
  reviewButton: document.getElementById("reviewButton"),
  statusBox: document.getElementById("statusBox"),
  healthBox: document.getElementById("healthBox"),
  resultPanel: document.getElementById("resultPanel"),
  metadataBox: document.getElementById("metadataBox"),
  summaryBox: document.getElementById("summaryBox"),
  criteriaGrid: document.getElementById("criteriaGrid"),
  orthographyBox: document.getElementById("orthographyBox"),
  downloadButton: document.getElementById("downloadButton"),
};

let currentResult = null;
let assignmentVisible = false;

const FORM_GUIDES = {
  auto: {
    guide:
      "Automatische Erkennung ist möglich. Für eine verlässliche Korrektur ist die manuelle Formwahl jedoch besser, vor allem bei Erörterungen.",
    example:
      "Beispiel: Analysieren Sie den Text und verfassen Sie eine passende, klar strukturierte Stellungnahme.",
    topicPlaceholder:
      "z. B. Sollten soziale Medien im Unterricht gezielt eingesetzt werden?",
    thesisLabel: "Leitfrage / These des Aufsatzes",
    thesisPlaceholder:
      "z. B. Der Text soll eine klare Kernfrage verfolgen oder eine tragfähige Hauptthese entfalten.",
  },
  essay: {
    guide:
      "Der Essay braucht eine eigenständige, reflektierte Position. Wichtig sind gedankliche Tiefe, persönliche Stimme und ein klarer roter Faden.",
    example:
      "Beispiel: Setzen Sie sich in essayistischer Form persönlich und differenziert mit der Frage auseinander, was gesellschaftliche Verantwortung heute bedeutet.",
    topicPlaceholder:
      "z. B. Was bedeutet Freiheit im digitalen Alltag?",
    thesisLabel: "Leitfrage / These des Aufsatzes",
    thesisPlaceholder:
      "z. B. Der Essay zeigt, dass Freiheit ohne Selbstbegrenzung in neue Abhängigkeiten umschlagen kann.",
  },
  speech: {
    guide:
      "Beim Redemanuskript zählen Adressatenbezug, klare Botschaft, wirkungsvolle Dramaturgie und ein redeartiger Stil.",
    example:
      "Beispiel: Verfassen Sie ein Redemanuskript für eine Maturfeier und überzeugen Sie Ihr Publikum davon, dass Bildung Mut zur Verantwortung verlangt.",
    topicPlaceholder:
      "z. B. Warum Verantwortung zur Bildung gehört",
    thesisLabel: "Leitgedanke / Kernbotschaft der Rede",
    thesisPlaceholder:
      "z. B. Die Rede soll zeigen, dass Bildung erst dann wirksam wird, wenn sie in verantwortliches Handeln führt.",
  },
  linear_discussion: {
    guide:
      "Die lineare Erörterung braucht eine klare Grundhaltung. Die Argumente müssen steigernd angeordnet sein und in ein begründetes Gesamturteil münden.",
    example:
      "Beispiel: Warum ist eine gute Schulbildung heute wichtiger denn je?",
    topicPlaceholder:
      "z. B. Warum ist eine gute Schulbildung heute wichtiger denn je?",
    thesisLabel: "Leitfrage / Grundthese der Erörterung",
    thesisPlaceholder:
      "z. B. Der Aufsatz soll begründen, warum breite Bildung langfristig mehr Chancen und Urteilskraft schafft.",
  },
  dialectical_discussion: {
    guide:
      "Die dialektische Erörterung muss die Streitfrage offenlegen, Pro und Contra klar führen, einen Wendepunkt markieren und auf ein bewusst starkes Schlussargument zusteuern.",
    example:
      "Beispiel: Erörtern Sie die Vor- und Nachteile des frühen Computereinsatzes im Kindergarten und nehmen Sie am Schluss Stellung.",
    topicPlaceholder:
      "z. B. Sollten Computer bereits im Kindergarten eingeführt werden?",
    thesisLabel: "Leitfrage / vorläufige Position der Erörterung",
    thesisPlaceholder:
      "z. B. Der Aufsatz soll abwägen, ob der Nutzen früher Digitalisierung die pädagogischen Risiken wirklich überwiegt.",
  },
};

elements.healthButton.addEventListener("click", checkHealth);
elements.reviewButton.addEventListener("click", generateReview);
elements.downloadButton.addEventListener("click", downloadReview);
elements.assignmentToggle.addEventListener("click", toggleAssignment);
elements.exampleAssignmentButton.addEventListener("click", applyExampleAssignment);
elements.documentType.addEventListener("change", syncFormGuide);

syncFormGuide();

async function checkHealth() {
  setHealth("LM Studio wird geprüft ...", "");
  try {
    const response = await fetch("/api/health");
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "LM Studio ist nicht erreichbar.");
    }

    const lines = [
      payload.privacy_notice,
      `Verbindung erfolgreich: ${payload.base_url}`,
      `Geladene Modelle: ${payload.models.join(", ")}`,
      `Standardmodell: ${payload.selected_model}`,
    ];
    setHealth(lines.join("\n"), "ok");
  } catch (error) {
    setHealth(error.message, "error");
  }
}

async function generateReview() {
  const file = elements.docxFile.files[0];
  if (!file) {
    setStatus("Bitte zuerst ein DOCX-Dokument auswählen.", "error");
    return;
  }
  if (!elements.thesisInput.value.trim()) {
    setStatus("Bitte die Leitfrage oder These des Aufsatzes angeben.", "error");
    elements.thesisInput.focus();
    return;
  }

  setStatus("DOCX wird lokal vorbereitet und an LM Studio übergeben ...", "");
  elements.reviewButton.disabled = true;

  try {
    const documentBase64 = await readFileAsBase64(file);
    const response = await fetch("/api/review", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        filename: file.name,
        document_base64: documentBase64,
        document_type: elements.documentType.value,
        topic: elements.topicInput.value.trim(),
        thesis: elements.thesisInput.value.trim(),
        assignment_text: assignmentVisible ? elements.assignmentInput.value.trim() : "",
        gym_level: elements.gymLevel.value,
        model: elements.model.value.trim(),
      }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Die Auswertung ist fehlgeschlagen.");
    }

    currentResult = payload;
    renderResult(payload.review);
    setStatus("Korrigiertes DOCX wurde erfolgreich erzeugt.", "ok");
  } catch (error) {
    currentResult = null;
    elements.resultPanel.classList.add("hidden");
    setStatus(error.message, "error");
  } finally {
    elements.reviewButton.disabled = false;
  }
}

function renderResult(review) {
  elements.resultPanel.classList.remove("hidden");
  const metadata = [];
  if (review.privacy_notice) {
    metadata.push(`<strong>${escapeHtml(review.privacy_notice)}</strong>`);
  }
  metadata.push(`Form: ${escapeHtml(review.document_type_label || "nicht bestimmt")}`);
  if (review.topic) {
    metadata.push(`Thema: ${escapeHtml(review.topic)}`);
  }
  if (review.thesis) {
    metadata.push(`Leitfrage / These: ${escapeHtml(review.thesis)}`);
  }
  if (review.assignment_text) {
    metadata.push(`Aufgabenstellung: ${formatText(review.assignment_text)}`);
  }
  elements.metadataBox.innerHTML = `
    <h3>Bewertungsrahmen</h3>
    <p>${metadata.join("<br />")}</p>
  `;
  elements.summaryBox.innerHTML = `
    <h3>Kurzzusammenfassung</h3>
    <p>${formatText(review.summary || "Keine Zusammenfassung vorhanden.")}</p>
  `;

  const labels = {
    inhalt: "Kriterium 1 - Inhalt",
    aufbau: "Kriterium 2 - Aufbau",
    ausdruck: "Kriterium 3 - Ausdruck",
  };
  elements.criteriaGrid.innerHTML = ["inhalt", "aufbau", "ausdruck"]
    .map((key) => {
      const entry = review.criteria_comments[key];
      return `
        <article class="criteria-card">
          <h3>${labels[key]}</h3>
          <div class="score">Teilnote ${Number(entry.score).toFixed(2)}</div>
          <p>${formatText(entry.comment)}</p>
        </article>
      `;
    })
    .join("");

  const orthography = review.orthography;
  elements.orthographyBox.innerHTML = `
    <h3>Kriterium 4 - Sprachliche Korrektheit</h3>
    <div class="score">Teilnote ${Number(orthography.grade).toFixed(2)}</div>
    <p>${formatText(orthography.comment)}</p>
  `;
}

function toggleAssignment() {
  assignmentVisible = !assignmentVisible;
  elements.assignmentWrap.classList.toggle("hidden", !assignmentVisible);
  elements.assignmentToggle.textContent = assignmentVisible
    ? "Aufgabenstellung ausblenden"
    : "Aufgabenstellung eingeben";
}

function applyExampleAssignment() {
  const guide = FORM_GUIDES[elements.documentType.value] || FORM_GUIDES.auto;
  if (!assignmentVisible) {
    toggleAssignment();
  }
  elements.assignmentInput.value = guide.example.replace(/^Beispiel:\s*/i, "");
  if (!elements.topicInput.value.trim()) {
    elements.topicInput.placeholder = guide.topicPlaceholder;
  }
}

function syncFormGuide() {
  const guide = FORM_GUIDES[elements.documentType.value] || FORM_GUIDES.auto;
  elements.formGuideText.textContent = guide.guide;
  elements.exampleAssignmentText.textContent = guide.example;
  elements.topicInput.placeholder = guide.topicPlaceholder;
  elements.thesisLabel.textContent = guide.thesisLabel;
  elements.thesisInput.placeholder = guide.thesisPlaceholder;
}

function downloadReview() {
  if (!currentResult) {
    return;
  }
  const blob = base64ToBlob(
    currentResult.reviewed_document_base64,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  );
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = currentResult.download_name || "korrigiert.docx";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 500);
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const commaIndex = result.indexOf(",");
      resolve(commaIndex >= 0 ? result.slice(commaIndex + 1) : result);
    };
    reader.onerror = () => reject(new Error("Die Datei konnte nicht gelesen werden."));
    reader.readAsDataURL(file);
  });
}

function base64ToBlob(base64, mimeType) {
  const bytes = atob(base64);
  const buffer = new Uint8Array(bytes.length);
  for (let index = 0; index < bytes.length; index += 1) {
    buffer[index] = bytes.charCodeAt(index);
  }
  return new Blob([buffer], { type: mimeType });
}

function setStatus(message, variant) {
  elements.statusBox.textContent = message;
  elements.statusBox.className = variant ? `status ${variant}` : "status";
}

function setHealth(message, variant) {
  elements.healthBox.textContent = message;
  elements.healthBox.className = variant ? `health ${variant}` : "health";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatText(value) {
  return escapeHtml(value).replaceAll("\n", "<br />");
}
