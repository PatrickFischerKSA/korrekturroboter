const elements = {
  docxFile: document.getElementById("docxFile"),
  uploadBox: document.getElementById("uploadBox"),
  fileStatus: document.getElementById("fileStatus"),
  dossierFile: document.getElementById("dossierFile"),
  dossierUploadBox: document.getElementById("dossierUploadBox"),
  dossierStatus: document.getElementById("dossierStatus"),
  dossierCandidateSection: document.getElementById("dossierCandidateSection"),
  dossierCandidateList: document.getElementById("dossierCandidateList"),
  confirmDossierButton: document.getElementById("confirmDossierButton"),
  resetDossierButton: document.getElementById("resetDossierButton"),
  dossierConfirmStatus: document.getElementById("dossierConfirmStatus"),
  documentType: document.getElementById("documentType"),
  formQuickButtons: Array.from(document.querySelectorAll(".quick-form-button")),
  formGuideText: document.getElementById("formGuideText"),
  exampleAssignmentButton: document.getElementById("exampleAssignmentButton"),
  exampleAssignmentText: document.getElementById("exampleAssignmentText"),
  topicInput: document.getElementById("topicInput"),
  thesisLabel: document.getElementById("thesisLabel"),
  thesisInput: document.getElementById("thesisInput"),
  assignmentToggle: document.getElementById("assignmentToggle"),
  dossierDetectButton: document.getElementById("dossierDetectButton"),
  assignmentWrap: document.getElementById("assignmentWrap"),
  assignmentInput: document.getElementById("assignmentInput"),
  gymLevel: document.getElementById("gymLevel"),
  schoolMode: document.getElementById("schoolMode"),
  schoolModeHint: document.getElementById("schoolModeHint"),
  model: document.getElementById("model"),
  healthButton: document.getElementById("healthButton"),
  reviewButton: document.getElementById("reviewButton"),
  resetButton: document.getElementById("resetButton"),
  statusBox: document.getElementById("statusBox"),
  warningBox: document.getElementById("warningBox"),
  healthBox: document.getElementById("healthBox"),
  resultPanel: document.getElementById("resultPanel"),
  metadataBox: document.getElementById("metadataBox"),
  summaryBox: document.getElementById("summaryBox"),
  sectionReportsBox: document.getElementById("sectionReportsBox"),
  criteriaGrid: document.getElementById("criteriaGrid"),
  orthographyBox: document.getElementById("orthographyBox"),
  downloadButton: document.getElementById("downloadButton"),
};

let currentResult = null;
let assignmentVisible = false;
let selectedFile = null;
let selectedDossier = null;
let dossierCandidates = [];
let confirmedDossierIndex = -1;
let activeDossierCandidateIndex = 0;
let dossierConfirmationRequired = false;
const PENDING_FILE_KEY = "korrekturroboter_pending_file";
const DEFAULT_MODEL_ID = "mistral-small-3.2-24b-instruct-2506-mlx";

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
elements.resetButton.addEventListener("click", resetFormState);
elements.downloadButton.addEventListener("click", downloadReview);
elements.assignmentToggle.addEventListener("click", toggleAssignment);
elements.exampleAssignmentButton.addEventListener("click", applyExampleAssignment);
elements.dossierDetectButton.addEventListener("click", detectDossierContext);
elements.confirmDossierButton.addEventListener("click", confirmSelectedDossierCandidate);
elements.resetDossierButton.addEventListener("click", resetDossierSelection);
elements.documentType.addEventListener("change", syncFormGuide);
elements.schoolMode.addEventListener("change", syncSchoolModeState);
elements.formQuickButtons.forEach((button) => {
  button.addEventListener("click", () => setDocumentTypeFromQuickButton(button.dataset.form || "auto"));
});
elements.docxFile.addEventListener("change", handleFileInput);
elements.dossierFile.addEventListener("change", handleDossierInput);
elements.uploadBox.addEventListener("dragover", handleDragOver);
elements.uploadBox.addEventListener("dragleave", handleDragLeave);
elements.uploadBox.addEventListener("drop", handleDrop);
elements.dossierUploadBox.addEventListener("dragover", handleDossierDragOver);
elements.dossierUploadBox.addEventListener("dragleave", handleDossierDragLeave);
elements.dossierUploadBox.addEventListener("drop", handleDossierDrop);
elements.dossierCandidateList.addEventListener("change", handleDossierCandidateListChange);

syncFormGuide();
elements.model.value = DEFAULT_MODEL_ID;
syncSchoolModeState();
updateReviewButtonState();
clearWarnings();
restorePendingFile();

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
    setHealth(buildLmStudioHelp(error.message), "error");
  }
}

async function generateReview() {
  const file = selectedFile;
  if (!file) {
    setStatus("Bitte zuerst ein DOCX-Dokument auswählen.", "error");
    return;
  }
  if (dossierConfirmationRequired) {
    setStatus("Bitte zuerst das erkannte Thema aus dem Prüfungsdossier bestätigen.", "error");
    return;
  }

  setStatus("DOCX wird lokal vorbereitet und an LM Studio übergeben ...", "");
  elements.reviewButton.disabled = true;

  try {
    const documentBase64 = await readFileAsBase64(file);
    const dossierBase64 = selectedDossier ? await readFileAsBase64(selectedDossier) : "";
    const response = await fetch("/api/review", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        filename: file.name,
        document_base64: documentBase64,
        dossier_name: selectedDossier ? selectedDossier.name : "",
        dossier_base64: dossierBase64,
        document_type: elements.documentType.value,
        topic: elements.topicInput.value.trim(),
        thesis: elements.thesisInput.value.trim(),
        assignment_text: assignmentVisible ? elements.assignmentInput.value.trim() : "",
        gym_level: elements.gymLevel.value,
        model: elements.model.value.trim(),
        school_mode: elements.schoolMode.checked,
      }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Die Auswertung ist fehlgeschlagen.");
    }

    currentResult = payload;
    renderResult(payload.review);
    showWarnings([
      ...buildDossierWarnings(payload.dossier_context || {}),
      ...buildReviewWarnings(payload.review || {}),
    ]);
    setStatus("Korrigiertes DOCX wurde erfolgreich erzeugt.", "ok");
  } catch (error) {
    currentResult = null;
    elements.resultPanel.classList.add("hidden");
    clearWarnings();
    setStatus(buildLmStudioHelp(error.message), "error");
  } finally {
    elements.reviewButton.disabled = false;
  }
}

function renderResult(review) {
  elements.resultPanel.classList.remove("hidden");
  const metadata = [];
  const dossierContext = currentResult?.dossier_context || {};
  if (review.privacy_notice) {
    metadata.push(`<strong>${escapeHtml(review.privacy_notice)}</strong>`);
  }
  if (dossierContext.match_label) {
    metadata.push(`Dossier-Abgleich: ${escapeHtml(dossierContext.match_label)}`);
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
  renderSectionReports(review.section_reports || []);

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

function renderSectionReports(sectionReports) {
  if (!Array.isArray(sectionReports) || !sectionReports.length) {
    elements.sectionReportsBox.innerHTML = "";
    elements.sectionReportsBox.classList.add("hidden");
    return;
  }

  elements.sectionReportsBox.classList.remove("hidden");
  elements.sectionReportsBox.innerHTML = `
    <h3>Zwischenberichte pro Abschnitt</h3>
    <p>Die Korrektur wurde abschnittsweise vorbereitet und danach zu einem Gesamtfeedback verdichtet. Hier siehst du die tragenden Zwischenbefunde.</p>
    <div class="section-report-list">
      ${sectionReports
        .map((report) => {
          const criteria = ["inhalt", "aufbau", "ausdruck"]
            .map((key) => {
              const entry = report.criteria_signals?.[key] || {};
              return `
                <div class="section-signal">
                  <strong>${escapeHtml(capitalize(key))}</strong>
                  <span class="score">Teilnote ${Number(entry.score || 4).toFixed(2)}</span>
                  <p>${formatText(entry.evidence || "Für diesen Aspekt liegt in diesem Abschnitt kein eigener Schwerpunkt vor.")}</p>
                </div>
              `;
            })
            .join("");

          return `
            <article class="section-report-card">
              <div class="section-report-head">
                <h4>${escapeHtml(report.label || "Abschnitt")}</h4>
                <span class="candidate-meta">${escapeHtml(report.range_label || "")}</span>
              </div>
              <p>${formatText(report.summary || "Keine Abschnittszusammenfassung vorhanden.")}</p>
              <div class="section-report-meta">
                <span class="candidate-meta">${escapeHtml(String(report.annotation_count || 0))} Textkommentare</span>
                <span class="candidate-meta">${escapeHtml(String(report.language_error_count || 0))} Sprachfehler</span>
              </div>
              <div class="section-signal-grid">
                ${criteria}
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function toggleAssignment() {
  assignmentVisible = !assignmentVisible;
  elements.assignmentWrap.classList.toggle("hidden", !assignmentVisible);
  elements.assignmentToggle.textContent = assignmentVisible
    ? "Aufgabenstellung ausblenden"
    : "Aufgabenstellung eingeben";
}

function handleFileInput(event) {
  const [file] = event.target.files || [];
  setSelectedFile(file || null);
}

function handleDossierInput(event) {
  const [file] = event.target.files || [];
  setSelectedDossier(file || null);
}

function handleDragOver(event) {
  event.preventDefault();
  elements.uploadBox.classList.add("dragover");
}

function handleDragLeave() {
  elements.uploadBox.classList.remove("dragover");
}

function handleDrop(event) {
  event.preventDefault();
  elements.uploadBox.classList.remove("dragover");
  const [file] = event.dataTransfer.files || [];
  setSelectedFile(file || null);
}

function handleDossierDragOver(event) {
  event.preventDefault();
  elements.dossierUploadBox.classList.add("dragover");
}

function handleDossierDragLeave() {
  elements.dossierUploadBox.classList.remove("dragover");
}

function handleDossierDrop(event) {
  event.preventDefault();
  elements.dossierUploadBox.classList.remove("dragover");
  const [file] = event.dataTransfer.files || [];
  setSelectedDossier(file || null);
}

function setSelectedFile(file) {
  if (!file) {
    selectedFile = null;
    elements.fileStatus.textContent = "Noch keine Datei geladen.";
    elements.fileStatus.className = "status";
    updateReviewButtonState();
    return;
  }

  const lowerName = file.name.toLowerCase();
  if (!lowerName.endsWith(".docx")) {
    selectedFile = null;
    elements.fileStatus.textContent = "Ungültige Datei: Bitte eine DOCX-Datei laden.";
    elements.fileStatus.className = "status error";
    setStatus("Bitte eine gültige DOCX-Datei laden.", "error");
    updateReviewButtonState();
    return;
  }

  selectedFile = file;
  const sizeKb = (file.size / 1024).toFixed(1);
  elements.fileStatus.textContent = `Datei geladen: ${file.name} (${sizeKb} KB). Bereit zur Korrektur.`;
  elements.fileStatus.className = "status ok";
  setStatus("Datei erfolgreich geladen. Du kannst die Korrektur jetzt starten.", "ok");
  if (selectedDossier) {
    dossierConfirmationRequired = true;
  }
  updateReviewButtonState();
  maybeAutoDetectDossierContext();
}

function setSelectedDossier(file) {
  if (!file) {
    selectedDossier = null;
    clearDossierCandidates();
    elements.dossierStatus.textContent = "Noch kein Prüfungsdossier geladen.";
    elements.dossierStatus.className = "status";
    updateReviewButtonState();
    return;
  }

  const lowerName = file.name.toLowerCase();
  if (!lowerName.endsWith(".docx") && !lowerName.endsWith(".txt") && !lowerName.endsWith(".pdf")) {
    selectedDossier = null;
    clearDossierCandidates();
    elements.dossierStatus.textContent = "Ungültige Datei: Bitte ein Dossier als DOCX, TXT oder PDF laden.";
    elements.dossierStatus.className = "status error";
    setStatus("Das Prüfungsdossier muss als DOCX, TXT oder PDF vorliegen.", "error");
    updateReviewButtonState();
    return;
  }

  selectedDossier = file;
  clearDossierCandidates();
  const sizeKb = (file.size / 1024).toFixed(1);
  elements.dossierStatus.textContent =
    `Prüfungsdossier geladen: ${file.name} (${sizeKb} KB). Thema und Aufgabenstellung können automatisch erkannt werden.`;
  elements.dossierStatus.className = "status ok";
  if (selectedFile) {
    dossierConfirmationRequired = true;
  }
  updateReviewButtonState();
  maybeAutoDetectDossierContext();
}

async function maybeAutoDetectDossierContext() {
  if (!selectedFile || !selectedDossier) {
    return;
  }
  await detectDossierContext(true);
}

async function detectDossierContext(silent = false) {
  if (!selectedFile) {
    setStatus("Für die Themen-Erkennung muss zuerst der Aufsatz geladen werden.", "error");
    return;
  }
  if (!selectedDossier) {
    setStatus("Für die Themen-Erkennung fehlt das Prüfungsdossier.", "error");
    return;
  }

  if (!silent) {
    setStatus("Prüfungsdossier wird mit dem Aufsatz abgeglichen ...", "");
  }

  try {
    const documentBase64 = await readFileAsBase64(selectedFile);
    const dossierBase64 = await readFileAsBase64(selectedDossier);
    const response = await fetch("/api/dossier-detect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        filename: selectedFile.name,
        document_base64: documentBase64,
        dossier_name: selectedDossier.name,
        dossier_base64: dossierBase64,
        school_mode: elements.schoolMode.checked,
      }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "Das Prüfungsdossier konnte nicht ausgewertet werden.");
    }

    applyDetectedContext(payload.dossier_context || {});
    showWarnings(buildDossierWarnings(payload.dossier_context || {}));
    if (!silent) {
      setStatus("Themenliste aus dem Prüfungsdossier wurde erzeugt. Bitte das passende Thema bestätigen.", "ok");
    }
  } catch (error) {
    clearWarnings();
    if (!silent) {
      setStatus(error.message, "error");
    } else {
      elements.dossierStatus.textContent = `Prüfungsdossier geladen, aber noch nicht automatisch erkannt: ${error.message}`;
      elements.dossierStatus.className = "status error";
    }
  }
}

function applyDetectedContext(context) {
  dossierCandidates = Array.isArray(context.candidates) ? context.candidates : [];
  if (!dossierCandidates.length && (context.topic || context.assignment_text)) {
    dossierCandidates = [
      {
        topic: context.topic || "Erkanntes Thema",
        assignment_text: context.assignment_text || "",
        document_type: context.document_type || "auto",
        document_type_label: context.document_type_label || "",
        match_score: context.match_score || 1,
        match_label: context.match_label || "Erkannt",
      },
    ];
  }
  dossierCandidates = dossierCandidates.map((candidate) => ({
    ...candidate,
    selected_document_type: candidate.selected_document_type || candidate.document_type || "auto",
  }));
  activeDossierCandidateIndex = 0;
  confirmedDossierIndex = -1;
  dossierConfirmationRequired = dossierCandidates.length > 0;
  renderDossierCandidates();
  if (context.match_label) {
    elements.dossierStatus.textContent = context.match_label;
    elements.dossierStatus.className = "status ok";
  }
  updateReviewButtonState();
}

function buildDossierWarnings(context) {
  const warnings = [...(context.warnings || [])];
  if (context.pipeline?.mode === "two_stage_local") {
    warnings.unshift(
      `Zweistufige Dossieranalyse aktiv: ${context.pipeline.stage_1 || "Themen extrahieren"} ${context.pipeline.stage_2 || "Abgleich mit dem Aufsatz"}`.trim()
    );
  }
  return warnings;
}

function buildReviewWarnings(review) {
  const warnings = [...(review.warnings || [])];
  if (review.pipeline?.mode === "two_stage_review") {
    warnings.unshift(
      `Zweistufige Korrekturanalyse aktiv: ${review.pipeline.stage_1 || "Abschnittsanalyse"} ${review.pipeline.stage_2 || "Gesamtauswertung"}`.trim()
    );
  }
  return warnings;
}

function renderDossierCandidates() {
  if (!dossierCandidates.length) {
    elements.dossierCandidateSection.classList.add("hidden");
    elements.dossierCandidateList.innerHTML = "";
    elements.dossierConfirmStatus.textContent = "Noch kein Thema bestätigt.";
    return;
  }

  elements.dossierCandidateSection.classList.remove("hidden");
  elements.dossierCandidateList.innerHTML = dossierCandidates
    .map((candidate, index) => {
      const checked = index === activeDossierCandidateIndex ? "checked" : "";
      const title = candidate.topic || `Thema ${index + 1}`;
      const assignment = truncateText(candidate.assignment_text || "Keine Aufgabenstellung erkannt.", 180);
      const typeLabel = getDocumentTypeLabel(candidate.document_type || "auto");
      const selectedType = candidate.selected_document_type || candidate.document_type || "auto";
      const manualChanged = selectedType !== (candidate.document_type || "auto");
      const score = Number(candidate.match_score || 0);
      return `
        <label class="candidate-option">
          <span class="candidate-row">
            <input type="radio" name="dossierCandidate" value="${index}" ${checked} />
            <span>
              <span class="candidate-head">
                <strong class="candidate-title">${escapeHtml(title)}</strong>
                <span class="candidate-meta">Erkannt: ${escapeHtml(typeLabel)}</span>
                ${manualChanged ? `<span class="candidate-meta candidate-meta-accent">Manuell: ${escapeHtml(getDocumentTypeLabel(selectedType))}</span>` : ""}
                <span class="candidate-meta">Treffer ${escapeHtml(score.toString())}</span>
              </span>
              <div class="candidate-controls">
                <label class="candidate-form-field">
                  <span>Textform ändern</span>
                  <select class="candidate-form-select" data-index="${index}">
                    ${buildCandidateFormOptions(selectedType)}
                  </select>
                </label>
              </div>
              <p class="candidate-text"><strong>Aufgabe:</strong> ${formatText(assignment)}</p>
            </span>
          </span>
        </label>
      `;
    })
    .join("");
  elements.dossierConfirmStatus.textContent = "Noch kein Thema bestätigt.";
}

function confirmSelectedDossierCandidate() {
  if (!dossierCandidates.length) {
    setStatus("Es liegt noch keine Themenliste aus dem Prüfungsdossier vor.", "error");
    return;
  }

  const selectedOption = document.querySelector('input[name="dossierCandidate"]:checked');
  const index = Number(selectedOption?.value ?? activeDossierCandidateIndex);
  const candidate = dossierCandidates[index];
  if (!candidate) {
    setStatus("Bitte zuerst ein Thema aus der Liste wählen.", "error");
    return;
  }

  activeDossierCandidateIndex = index;
  confirmedDossierIndex = index;
  dossierConfirmationRequired = false;
  applyConfirmedCandidate(candidate);
  const selectedType = candidate.selected_document_type || candidate.document_type || "auto";
  const confirmSuffix = selectedType !== (candidate.document_type || "auto") ? " - Form manuell angepasst" : "";
  elements.dossierConfirmStatus.textContent = `Bestätigt: ${candidate.topic} (${getDocumentTypeLabel(selectedType)})${confirmSuffix}`;
  elements.dossierStatus.textContent = `Bestätigtes Thema aus dem Prüfungsdossier: ${candidate.topic}`;
  elements.dossierStatus.className = "status ok";
  updateReviewButtonState();
  setStatus("Thema aus dem Prüfungsdossier bestätigt. Die Korrektur kann jetzt starten.", "ok");
}

function applyConfirmedCandidate(candidate) {
  const selectedType = candidate.selected_document_type || candidate.document_type || "auto";
  elements.documentType.value = selectedType;
  syncFormGuide();
  if (candidate.topic) {
    elements.topicInput.value = candidate.topic;
  }
  if (candidate.assignment_text) {
    if (!assignmentVisible) {
      toggleAssignment();
    }
    elements.assignmentInput.value = candidate.assignment_text;
  }
}

function handleDossierCandidateListChange(event) {
  const target = event.target;
  if (!(target instanceof Element)) {
    return;
  }
  if (target instanceof HTMLInputElement && target.name === "dossierCandidate") {
    const index = Number(target.value ?? -1);
    const candidate = dossierCandidates[index];
    if (candidate) {
      activeDossierCandidateIndex = index;
      elements.documentType.value = candidate.selected_document_type || candidate.document_type || "auto";
      syncFormGuide();
    }
    return;
  }
  if (!(target instanceof HTMLSelectElement) || !target.classList.contains("candidate-form-select")) {
    return;
  }
  const index = Number(target.dataset.index ?? -1);
  if (!Number.isInteger(index) || index < 0 || index >= dossierCandidates.length) {
    return;
  }
  dossierCandidates[index].selected_document_type = target.value;
  activeDossierCandidateIndex = index;
  renderDossierCandidates();
  const selectedOption = document.querySelector('input[name="dossierCandidate"]:checked');
  if (Number(selectedOption?.value ?? -1) === index) {
    elements.documentType.value = target.value;
    syncFormGuide();
  }
}

function resetDossierSelection() {
  selectedDossier = null;
  activeDossierCandidateIndex = 0;
  elements.dossierFile.value = "";
  clearDossierCandidates();
  elements.dossierStatus.textContent = "Noch kein Prüfungsdossier geladen.";
  elements.dossierStatus.className = "status";
  elements.topicInput.value = "";
  elements.assignmentInput.value = "";
  elements.documentType.value = "auto";
  syncFormGuide();
  clearWarnings();
  updateReviewButtonState();
  setStatus("Themenblock wurde zurückgesetzt. Du kannst jetzt ein neues Dossier laden oder die Form manuell festlegen.", "ok");
}

function clearDossierCandidates() {
  dossierCandidates = [];
  activeDossierCandidateIndex = 0;
  confirmedDossierIndex = -1;
  dossierConfirmationRequired = false;
  elements.dossierCandidateSection.classList.add("hidden");
  elements.dossierCandidateList.innerHTML = "";
  elements.dossierConfirmStatus.textContent = "Noch kein Thema bestätigt.";
}

function updateReviewButtonState() {
  elements.reviewButton.disabled = !selectedFile || dossierConfirmationRequired;
}

function resetFormState() {
  currentResult = null;
  assignmentVisible = false;
  selectedFile = null;
  selectedDossier = null;
  clearDossierCandidates();

  elements.docxFile.value = "";
  elements.dossierFile.value = "";
  elements.documentType.value = "auto";
  elements.topicInput.value = "";
  elements.thesisInput.value = "";
  elements.assignmentInput.value = "";
  elements.assignmentWrap.classList.add("hidden");
  elements.assignmentToggle.textContent = "Aufgabenstellung eingeben";
  elements.gymLevel.value = "1";
  elements.schoolMode.checked = true;
  elements.model.value = DEFAULT_MODEL_ID;
  elements.fileStatus.textContent = "Noch keine Datei geladen.";
  elements.fileStatus.className = "status";
  elements.dossierStatus.textContent = "Noch kein Prüfungsdossier geladen.";
  elements.dossierStatus.className = "status";
  elements.resultPanel.classList.add("hidden");
  elements.healthBox.innerHTML = "";
  clearWarnings();
  setStatus("Alle Eingaben wurden zurückgesetzt.", "ok");
  syncSchoolModeState();
  syncFormGuide();
  updateReviewButtonState();
}

function restorePendingFile() {
  const raw = sessionStorage.getItem(PENDING_FILE_KEY);
  if (!raw) {
    return;
  }
  sessionStorage.removeItem(PENDING_FILE_KEY);

  try {
    const payload = JSON.parse(raw);
    const bytes = base64ToUint8Array(payload.base64);
    const file = new File([bytes], payload.name || "aufsatz.docx", {
      type: payload.type || "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    setSelectedFile(file);
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") === "1") {
      setStatus("Demo-Dokument geladen. Du kannst den Ablauf sofort testen.", "ok");
    }
  } catch (error) {
    setSelectedFile(null);
    setStatus("Die vorbereitete Datei konnte nicht übernommen werden.", "error");
  }
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
  elements.thesisLabel.textContent = `${guide.thesisLabel} (optional)`;
  elements.thesisInput.placeholder = guide.thesisPlaceholder;
  syncQuickFormButtons();
}

function syncSchoolModeState() {
  if (elements.schoolMode.checked) {
    elements.model.value = DEFAULT_MODEL_ID;
    elements.model.disabled = true;
    elements.schoolModeHint.textContent =
      "Fixes Standardmodell, kompaktere Analysegrenzen und ruhigere lokale Läufe für längere Texte.";
    return;
  }

  elements.model.disabled = false;
  elements.schoolModeHint.textContent =
    "Freier Modus: Modellkennung ist anpassbar. Das ist flexibler, aber bei lokalen langen Texten weniger stabil.";
}

function setDocumentTypeFromQuickButton(value) {
  elements.documentType.value = value;
  syncFormGuide();
}

function syncQuickFormButtons() {
  elements.formQuickButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.form === elements.documentType.value);
  });
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
  return new Blob([base64ToUint8Array(base64)], { type: mimeType });
}

function base64ToUint8Array(base64) {
  const bytes = atob(base64);
  const buffer = new Uint8Array(bytes.length);
  for (let index = 0; index < bytes.length; index += 1) {
    buffer[index] = bytes.charCodeAt(index);
  }
  return buffer;
}

function setStatus(message, variant) {
  elements.statusBox.innerHTML = formatStatusMarkup(message);
  elements.statusBox.className = variant ? `status ${variant}` : "status";
}

function setHealth(message, variant) {
  elements.healthBox.innerHTML = formatStatusMarkup(message);
  elements.healthBox.className = variant ? `health ${variant}` : "health";
}

function showWarnings(items) {
  const warnings = (items || []).filter(Boolean);
  if (!warnings.length) {
    clearWarnings();
    return;
  }
  elements.warningBox.innerHTML = formatStatusMarkup(warnings.join("\n"));
  elements.warningBox.className = "status warning";
  elements.warningBox.classList.remove("hidden");
}

function clearWarnings() {
  elements.warningBox.innerHTML = "";
  elements.warningBox.className = "status warning hidden";
}

function formatStatusMarkup(message) {
  return escapeHtml(message)
    .replaceAll("\n\n", "<br /><br />")
    .replaceAll("\n", "<br />");
}

function buildLmStudioHelp(message) {
  const normalized = String(message || "").trim();
  const lower = normalized.toLowerCase();
  if (lower.includes("connection refused") || lower.includes("could not connect") || lower.includes("nicht erreichbar")) {
    return [
      `LM Studio antwortet nicht auf http://127.0.0.1:1234/v1.`,
      `So behebst du das:`,
      `1. LM Studio öffnen.`,
      `2. Ein Modell laden oder herunterladen.`,
      `3. In LM Studio den lokalen Server auf Port 1234 starten.`,
      `4. Danach hier erneut auf "Lokales LM Studio prüfen" klicken.`,
      `Technische Meldung: ${normalized}`,
    ].join("\n");
  }
  if (lower.includes("keine geladenen modelle")) {
    return [
      `LM Studio läuft, aber es ist noch kein Modell geladen.`,
      `So behebst du das:`,
      `1. In LM Studio ein passendes lokales Modell laden.`,
      `2. Den lokalen Server aktiv lassen.`,
      `3. Danach die Prüfung erneut starten.`,
      `Technische Meldung: ${normalized}`,
    ].join("\n");
  }
  return normalized;
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

function truncateText(value, maxLength) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1).trimEnd()}…`;
}

function capitalize(value) {
  const text = String(value || "");
  return text ? `${text.charAt(0).toUpperCase()}${text.slice(1)}` : "";
}

function getDocumentTypeLabel(value) {
  switch (value) {
    case "essay":
      return "Essay";
    case "speech":
      return "Rede";
    case "linear_discussion":
      return "Lineare Erörterung";
    case "dialectical_discussion":
      return "Dialektische Erörterung";
    default:
      return "Weitere Formen";
  }
}

function buildCandidateFormOptions(selectedValue) {
  const options = [
    ["auto", "Weitere Formen"],
    ["essay", "Essay"],
    ["speech", "Rede"],
    ["linear_discussion", "Lineare Erörterung"],
    ["dialectical_discussion", "Dialektische Erörterung"],
  ];
  return options
    .map(([value, label]) => `<option value="${value}" ${value === selectedValue ? "selected" : ""}>${escapeHtml(label)}</option>`)
    .join("");
}
