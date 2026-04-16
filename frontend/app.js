"use strict";

const API_BASE_URL = "https://azure-translation-demo.onrender.com";
const AZURE_PROVIDER = "azure";
const OFF_PROVIDER = "off";
const PROVIDER_LABELS = {
	off: "Off",
	azure: "Azure Translator",
};

const sourceTextInput = document.getElementById("sourceText");
const targetLanguageSelect = document.getElementById("targetLanguage");
const translatedTextOutput = document.getElementById("translatedText");
const altTextReviewedCheckbox = document.getElementById("altTextReviewed");
const altTextReviewedContainer = document.getElementById("altTextReviewedContainer");
const sampleContentButton = document.getElementById("sampleContentBtn");
const adminToggle = document.getElementById("adminAutoTranslateEnabled");
const autoTranslateButton = document.getElementById("autoTranslateBtn");
const submitButton = document.getElementById("submitBtn");
const autoTranslateStatus = document.getElementById("autoTranslateStatus");
const openAdminPanelButton = document.getElementById("openAdminPanelBtn");
const closeAdminPanelButton = document.getElementById("closeAdminPanelBtn");
const adminPanelBackdrop = document.getElementById("adminPanelBackdrop");
const adminPanelModal = document.getElementById("adminPanelModal");
const adminPanelStatus = document.getElementById("adminPanelStatus");
const providerSettingsBody = document.getElementById("providerSettingsBody");
const saveProviderSettingsButton = document.getElementById("saveProviderSettingsBtn");
const submissionSuccessModal = document.getElementById("submissionSuccessModal");
const submissionSuccessBackdrop = document.getElementById("submissionSuccessBackdrop");
const closeSubmissionSuccessButton = document.getElementById(
	"closeSubmissionSuccessBtn"
);
const submissionSuccessMessage = document.getElementById("submissionSuccessMessage");

const DEMO_SAMPLE_CONTENTS = [
	"Try solving <math>x^2 + y^2 = z^2</math>. Visit <a href=\"https://example.com/lesson\">this lesson link</a> for details. The illustration is <img src=\"triangle.png\" alt=\"Right triangle with labeled sides\">.",
	"Read this announcement and summarize it in simple terms. Refer to <a href=\"https://example.com/policy\">the policy page</a> for the full context.",
	"Solve the equation <math>2x + 5 = 17</math> and explain each step in easy language for beginners.",
	"The product poster includes <img src=\"camera.jpg\" alt=\"Compact camera on a wooden desk\">. Keep the brand terms unchanged.",
	"Use this travel update with mixed content: <math>distance = speed * time</math> and <a href=\"https://example.com/travel-guide\">travel guide link</a>.",
];

const state = {
	autoTranslateEnabledByAdmin: false,
	isTranslating: false,
	isSubmitting: false,
	providerSettings: [],
	providerOptions: [AZURE_PROVIDER],
	nextSampleIndex: 0,
};

function providerLabel(provider) {
	return PROVIDER_LABELS[provider] ?? provider;
}

function sourceContainsImageTag(text) {
	return /<img\b/i.test(text);
}

function isImageReviewRequirementSatisfied() {
	const hasImageTag = sourceContainsImageTag(sourceTextInput.value);
	return !hasImageTag || altTextReviewedCheckbox.checked;
}

function syncAltTextReviewVisibility() {
	const hasImageTag = sourceContainsImageTag(sourceTextInput.value);
	if (altTextReviewedContainer) {
		altTextReviewedContainer.hidden = !hasImageTag;
	}

	if (!hasImageTag) {
		altTextReviewedCheckbox.checked = false;
	}
}

function hasRequiredSubmissionContent() {
	const sourceText = sourceTextInput.value.trim();
	const translatedText = translatedTextOutput.value.trim();
	return sourceText.length > 0 && translatedText.length > 0;
}

function getProviderSettingByLanguageCode(languageCode) {
	return (
		state.providerSettings.find(
			(setting) => setting.language_code === languageCode
		) ?? null
	);
}

function isAutoTranslateOffForSelectedLanguage() {
	const selectedSetting = getProviderSettingByLanguageCode(targetLanguageSelect.value);
	return selectedSetting?.provider === OFF_PROVIDER;
}

function getSelectedLanguageName() {
	const selectedSetting = getProviderSettingByLanguageCode(targetLanguageSelect.value);
	if (selectedSetting?.language_name) {
		return selectedSetting.language_name;
	}
	return targetLanguageSelect.options[targetLanguageSelect.selectedIndex]?.text ??
		targetLanguageSelect.value;
}

function getValidationStatusMessage() {
	if (isAutoTranslateOffForSelectedLanguage()) {
		return {
			message: `Auto-Translate is Off for ${getSelectedLanguageName()}.`,
			tone: "info",
		};
	}

	if (!isImageReviewRequirementSatisfied()) {
		return {
			message: "Image detected. Confirm alt-text review to enable submit.",
			tone: "info",
		};
	}

	if (!state.autoTranslateEnabledByAdmin) {
		return {
			message: "Auto-Translate is disabled by admin. Manual submit is still available.",
			tone: "info",
		};
	}

	return {
		message: "Ready to submit.",
		tone: "info",
	};
}

function getSubmissionBlockReason() {
	if (!hasRequiredSubmissionContent()) {
		return "Source and translated text are required before submit.";
	}

	if (!isImageReviewRequirementSatisfied()) {
		return "Source contains an <img> tag. Confirm alt-text review before submit.";
	}
	return null;
}

function setStatus(message, tone = "info") {
	autoTranslateStatus.textContent = message;
	autoTranslateStatus.classList.remove("status-success", "status-error");
	if (tone === "success") {
		autoTranslateStatus.classList.add("status-success");
		return;
	}
	if (tone === "error") {
		autoTranslateStatus.classList.add("status-error");
	}
}

function setAdminPanelStatus(message, tone = "info") {
	adminPanelStatus.textContent = message;
	adminPanelStatus.classList.remove("status-success", "status-error");
	if (tone === "success") {
		adminPanelStatus.classList.add("status-success");
		return;
	}
	if (tone === "error") {
		adminPanelStatus.classList.add("status-error");
	}
}

function syncActionButtonsState() {
	syncAltTextReviewVisibility();

	const hideAutoTranslate = isAutoTranslateOffForSelectedLanguage();
	autoTranslateButton.hidden = hideAutoTranslate;
	autoTranslateButton.disabled =
		hideAutoTranslate ||
		!state.autoTranslateEnabledByAdmin ||
		state.isTranslating;
	submitButton.disabled =
		getSubmissionBlockReason() !== null || state.isSubmitting;
}

function applyAutoTranslateAvailability(enabled) {
	state.autoTranslateEnabledByAdmin = enabled;
	adminToggle.checked = enabled;
	syncActionButtonsState();
	const status = getValidationStatusMessage();
	setStatus(status.message, status.tone);
}

function syncBodyModalState() {
	const submissionModalVisible = submissionSuccessModal
		? !submissionSuccessModal.classList.contains("hidden")
		: false;
	const hasVisibleModal =
		!adminPanelModal.classList.contains("hidden") ||
		submissionModalVisible;
	document.body.classList.toggle("modal-open", hasVisibleModal);
}

function setAdminPanelVisibility(visible) {
	adminPanelModal.classList.toggle("hidden", !visible);
	adminPanelModal.setAttribute("aria-hidden", String(!visible));
	syncBodyModalState();
}

function setSubmissionSuccessModalVisibility(visible) {
	if (!submissionSuccessModal) {
		return;
	}

	submissionSuccessModal.classList.toggle("hidden", !visible);
	submissionSuccessModal.setAttribute("aria-hidden", String(!visible));
	syncBodyModalState();
}

function clearInputFieldsAfterSubmission() {
	sourceTextInput.value = "";
	translatedTextOutput.value = "";
	altTextReviewedCheckbox.checked = false;
	syncActionButtonsState();
	const status = getValidationStatusMessage();
	setStatus(status.message, status.tone);
}

function openSubmissionSuccessModal(submissionId) {
	if (!submissionSuccessModal || !submissionSuccessMessage) {
		clearInputFieldsAfterSubmission();
		return;
	}

	const hasSubmissionId = Number.isInteger(submissionId);
	if (hasSubmissionId) {
		submissionSuccessMessage.textContent =
			`Submitted and stored in DB. Submission ID: ${submissionId}.`;
	} else {
		submissionSuccessMessage.textContent = "Submitted and stored in DB.";
	}

	setSubmissionSuccessModalVisibility(true);
}

function closeSubmissionSuccessModal() {
	setSubmissionSuccessModalVisibility(false);
	clearInputFieldsAfterSubmission();
}

function updateProviderSettingInState(languageCode, provider) {
	state.providerSettings = state.providerSettings.map((setting) => {
		if (setting.language_code !== languageCode) {
			return setting;
		}
		return {
			...setting,
			provider,
		};
	});
}

function syncTargetLanguageOptions() {
	if (state.providerSettings.length === 0) {
		return;
	}

	const previousValue = targetLanguageSelect.value;
	const sortedSettings = [...state.providerSettings].sort((left, right) =>
		left.language_name.localeCompare(right.language_name)
	);

	targetLanguageSelect.innerHTML = "";
	for (const setting of sortedSettings) {
		const option = document.createElement("option");
		option.value = setting.language_code;
		option.textContent = setting.language_name;
		targetLanguageSelect.append(option);
	}

	const stillAvailable = sortedSettings.some(
		(setting) => setting.language_code === previousValue
	);
	if (stillAvailable) {
		targetLanguageSelect.value = previousValue;
		return;
	}

	targetLanguageSelect.value = sortedSettings[0].language_code;
}

function renderProviderSettingsTable() {
	providerSettingsBody.innerHTML = "";

	if (state.providerSettings.length === 0) {
		const emptyRow = document.createElement("tr");
		const emptyCell = document.createElement("td");
		emptyCell.colSpan = 2;
		emptyCell.textContent = "No language settings available.";
		emptyRow.append(emptyCell);
		providerSettingsBody.append(emptyRow);
		return;
	}

	const sortedSettings = [...state.providerSettings].sort((left, right) =>
		left.language_name.localeCompare(right.language_name)
	);

	for (const setting of sortedSettings) {
		const row = document.createElement("tr");

		const languageCell = document.createElement("td");
		languageCell.textContent = setting.language_name;

		const providerCell = document.createElement("td");
		const providerSelect = document.createElement("select");
		providerSelect.className = "provider-select";
		providerSelect.dataset.languageCode = setting.language_code;

		const options =
			state.providerOptions.length > 0
				? state.providerOptions
				: [AZURE_PROVIDER];

		for (const provider of options) {
			const option = document.createElement("option");
			option.value = provider;
			option.textContent = providerLabel(provider);
			providerSelect.append(option);
		}

		providerSelect.value = setting.provider;
		providerSelect.addEventListener("change", (event) => {
			updateProviderSettingInState(setting.language_code, event.target.value);
			setAdminPanelStatus("Unsaved provider changes.");
		});

		providerCell.append(providerSelect);
		row.append(languageCell, providerCell);
		providerSettingsBody.append(row);
	}
}

async function fetchAdminConfig() {
	const response = await fetch(`${API_BASE_URL}/api/admin/config`);
	if (!response.ok) {
		throw new Error("Failed to load admin config.");
	}

	const config = await response.json();
	adminToggle.checked = Boolean(config.auto_translate_enabled);
	applyAutoTranslateAvailability(adminToggle.checked);
}

async function updateAdminConfig(enabled) {
	const response = await fetch(`${API_BASE_URL}/api/admin/config/auto-translate`, {
		method: "PATCH",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ auto_translate_enabled: enabled }),
	});

	if (!response.ok) {
		throw new Error("Failed to update admin config.");
	}

	const config = await response.json();
	applyAutoTranslateAvailability(Boolean(config.auto_translate_enabled));
}

async function fetchProviderSettings() {
	const response = await fetch(`${API_BASE_URL}/api/admin/provider-settings`);
	if (!response.ok) {
		throw new Error("Failed to load provider settings.");
	}

	const payload = await response.json();
	state.providerSettings = Array.isArray(payload.settings) ? payload.settings : [];
	state.providerOptions =
		Array.isArray(payload.provider_options) && payload.provider_options.length > 0
			? payload.provider_options
			: [AZURE_PROVIDER];

	syncTargetLanguageOptions();
	renderProviderSettingsTable();
}

async function saveProviderSettings() {
	setAdminPanelStatus("Saving provider settings...");

	const response = await fetch(`${API_BASE_URL}/api/admin/provider-settings`, {
		method: "PUT",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			settings: state.providerSettings,
		}),
	});

	const payload = await response.json().catch(() => ({}));
	if (!response.ok) {
		const message =
			typeof payload.detail === "string"
				? payload.detail
				: "Failed to save provider settings.";
		throw new Error(message);
	}

	state.providerSettings = Array.isArray(payload.settings) ? payload.settings : [];
	state.providerOptions =
		Array.isArray(payload.provider_options) && payload.provider_options.length > 0
			? payload.provider_options
			: [AZURE_PROVIDER];

	syncTargetLanguageOptions();
	renderProviderSettingsTable();
	setAdminPanelStatus("Provider settings saved.", "success");
}

async function openAdminPanel() {
	setAdminPanelVisibility(true);
	setAdminPanelStatus("Loading admin settings...");

	try {
		await Promise.all([fetchAdminConfig(), fetchProviderSettings()]);
		setAdminPanelStatus("Admin settings loaded.", "success");
	} catch (error) {
		console.error(error);
		setAdminPanelStatus(`Could not load admin settings: ${error.message}`, "error");
	}
}

function closeAdminPanel() {
	setAdminPanelVisibility(false);
}

async function autoTranslateContent() {
	const sourceText = sourceTextInput.value.trim();
	if (!sourceText) {
		setStatus("Enter source content before using Auto-Translate.", "error");
		return;
	}

	if (!state.autoTranslateEnabledByAdmin) {
		setStatus("Auto-Translate is disabled by admin.", "error");
		return;
	}

	if (isAutoTranslateOffForSelectedLanguage()) {
		setStatus(
			`Auto-Translate is Off for ${getSelectedLanguageName()} in Admin Panel.`,
			"error"
		);
		return;
	}

	state.isTranslating = true;
	syncActionButtonsState();
	setStatus("Translating content...");

	try {
		const response = await fetch(`${API_BASE_URL}/translate`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				source_text: sourceText,
				target_language: targetLanguageSelect.value,
			}),
		});

		const payload = await response.json().catch(() => ({}));
		if (!response.ok) {
			const message =
				typeof payload.detail === "string"
					? payload.detail
					: "Translation request failed.";
			throw new Error(message);
		}

		translatedTextOutput.value = payload.translated_text ?? "";
		if (payload.cached) {
			setStatus("Translation complete (Autogenerated from cache).", "success");
			return;
		}
		setStatus("Translation complete (Autogenerated from Azure Translator).", "success");
	} catch (error) {
		console.error(error);
		setStatus(`Translation failed: ${error.message}`, "error");
	} finally {
		state.isTranslating = false;
		syncActionButtonsState();
	}
}

async function submitFinalTranslation() {
	const blockReason = getSubmissionBlockReason();
	if (blockReason) {
		setStatus(blockReason, "error");
		return;
	}

	state.isSubmitting = true;
	syncActionButtonsState();
	setStatus("Saving final translation...");

	try {
		const response = await fetch(`${API_BASE_URL}/api/submissions`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				source_text: sourceTextInput.value,
				target_language: targetLanguageSelect.value,
				translated_text: translatedTextOutput.value,
				alt_text_reviewed: altTextReviewedCheckbox.checked,
			}),
		});

		const payload = await response.json().catch(() => ({}));
		if (!response.ok) {
			const message =
				typeof payload.detail === "string"
					? payload.detail
					: "Submit request failed.";
			throw new Error(message);
		}

		setStatus(
			`${payload.message ?? "Final translation saved."} (ID ${payload.submission_id})`,
			"success"
		);
		openSubmissionSuccessModal(payload.submission_id);
	} catch (error) {
		console.error(error);
		setStatus(`Submit failed: ${error.message}`, "error");
	} finally {
		state.isSubmitting = false;
		syncActionButtonsState();
	}
}

sampleContentButton.addEventListener("click", () => {
	const sampleCount = DEMO_SAMPLE_CONTENTS.length;
	const nextIndex = state.nextSampleIndex % sampleCount;
	sourceTextInput.value = DEMO_SAMPLE_CONTENTS[nextIndex];
	state.nextSampleIndex = (nextIndex + 1) % sampleCount;

	syncActionButtonsState();
	if (!isImageReviewRequirementSatisfied()) {
		setStatus("Sample content loaded. Confirm alt-text review to enable submit.");
		return;
	}
	setStatus("Sample content loaded.");
});

autoTranslateButton.addEventListener("click", () => {
	void autoTranslateContent();
});

submitButton.addEventListener("click", () => {
	void submitFinalTranslation();
});

openAdminPanelButton.addEventListener("click", () => {
	void openAdminPanel();
});

closeAdminPanelButton.addEventListener("click", closeAdminPanel);
adminPanelBackdrop.addEventListener("click", closeAdminPanel);
if (closeSubmissionSuccessButton) {
	closeSubmissionSuccessButton.addEventListener("click", closeSubmissionSuccessModal);
}

if (submissionSuccessBackdrop) {
	submissionSuccessBackdrop.addEventListener("click", closeSubmissionSuccessModal);
}

document.addEventListener("keydown", (event) => {
	if (event.key !== "Escape") {
		return;
	}

	if (submissionSuccessModal && !submissionSuccessModal.classList.contains("hidden")) {
		closeSubmissionSuccessModal();
		return;
	}

	if (!adminPanelModal.classList.contains("hidden")) {
		closeAdminPanel();
	}
});

saveProviderSettingsButton.addEventListener("click", async () => {
	try {
		await saveProviderSettings();
		closeAdminPanel();
		syncActionButtonsState();
		const status = getValidationStatusMessage();
		setStatus(status.message, status.tone);
	} catch (error) {
		console.error(error);
		setAdminPanelStatus(`Could not save provider settings: ${error.message}`, "error");
	}
});

sourceTextInput.addEventListener("input", () => {
	syncActionButtonsState();
	const status = getValidationStatusMessage();
	setStatus(status.message, status.tone);
});

targetLanguageSelect.addEventListener("change", () => {
	syncActionButtonsState();
	const status = getValidationStatusMessage();
	setStatus(status.message, status.tone);
});

altTextReviewedCheckbox.addEventListener("change", () => {
	syncActionButtonsState();
	const status = getValidationStatusMessage();
	setStatus(status.message, status.tone);
});

translatedTextOutput.addEventListener("input", () => {
	syncActionButtonsState();
});

adminToggle.addEventListener("change", async (event) => {
	const previousValue = state.autoTranslateEnabledByAdmin;
	const nextValue = event.target.checked;
	try {
		await updateAdminConfig(nextValue);
		setAdminPanelStatus("Automatic translation setting updated.", "success");
	} catch (error) {
		console.error(error);
		adminToggle.checked = previousValue;
		applyAutoTranslateAvailability(previousValue);
		setAdminPanelStatus("Could not update automatic translation setting.", "error");
		setStatus("Could not update admin setting. Try again.", "error");
	}
});

Promise.all([fetchAdminConfig(), fetchProviderSettings()])
	.then(() => {
		syncActionButtonsState();
	})
	.catch((error) => {
		console.error(error);
		applyAutoTranslateAvailability(false);
		setStatus("Could not load admin settings. Auto-Translate disabled.", "error");
		setAdminPanelStatus("Could not load admin settings.", "error");
	});
