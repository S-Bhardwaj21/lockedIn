const vscode = require("vscode");
const fs = require("fs");
const path = require("path");

const RUNTIME_DIR = "C:\\Users\\Shreya\\lockedin\\runtime";
const CONTEXT_FILE = path.join(RUNTIME_DIR, "vscode_context.json");
const RESTORE_FILE = path.join(RUNTIME_DIR, "vscode_restore.json");
const STATUS_FILE = path.join(RUNTIME_DIR, "vscode_restore_status.json");

function ensureRuntime() {
    fs.mkdirSync(RUNTIME_DIR, { recursive: true });
}

function writeJson(file, data) {
    ensureRuntime();
    const temp = `${file}.tmp`;
    fs.writeFileSync(temp, JSON.stringify(data, null, 2), "utf8");
    fs.renameSync(temp, file);
}

function getContext() {
    const editor = vscode.window.activeTextEditor;
    const tabs = [];

    for (const group of vscode.window.tabGroups.all) {
        for (const tab of group.tabs) {
            const uri = tab.input?.uri;
            if (uri && uri.scheme === "file") {
                tabs.push({
                    label: tab.label,
                    path: uri.fsPath
                });
            }
        }
    }

    const context = {
        timestamp: Date.now(),
        activeFile: null,
        line: null,
        column: null,
        tabs
    };

    if (editor) {
        const position = editor.selection.active;
        context.activeFile = editor.document.uri.fsPath;
        context.line = position.line + 1;
        context.column = position.character + 1;
    }

    return context;
}

function captureContext() {
    writeJson(CONTEXT_FILE, getContext());
}

function writeStatus(status, message, extra = {}) {
    writeJson(STATUS_FILE, {
        timestamp: Date.now(),
        status,
        message,
        ...extra
    });
}

async function restoreContext(request) {
    writeStatus("received", "Restore request received.", {
        activeFile: request.activeFile,
        line: request.line,
        column: request.column,
        tabs: request.tabs
    });

    try {
        if (!request.activeFile) {
            throw new Error("No active file in restore request.");
        }

        for (const file of request.tabs || []) {
            if (!fs.existsSync(file)) {
                continue;
            }

            const document = await vscode.workspace.openTextDocument(file);

            await vscode.window.showTextDocument(document, {
                preview: false,
                preserveFocus: true
            });
        }

        const activeFile = request.activeFile;

        if (!fs.existsSync(activeFile)) {
            throw new Error(`Active file does not exist: ${activeFile}`);
        }

        const document = await vscode.workspace.openTextDocument(activeFile);

        const editor = await vscode.window.showTextDocument(document, {
            viewColumn: vscode.ViewColumn.Active,
            preview: false,
            preserveFocus: false
        });

        const line = Math.max(1, request.line || 1);
        const column = Math.max(1, request.column || 1);

        const lineIndex = Math.min(
            line - 1,
            document.lineCount - 1
        );

        const maxColumn = document.lineAt(lineIndex).text.length;

        const columnIndex = Math.min(
            column - 1,
            maxColumn
        );

        const position = new vscode.Position(
            lineIndex,
            columnIndex
        );

        editor.selection = new vscode.Selection(
            position,
            position
        );

        editor.revealRange(
            new vscode.Range(position, position),
            vscode.TextEditorRevealType.InCenter
        );

        writeStatus("success", "Restore completed.", {
            activeFile,
            line: line,
            column: column,
            actualActiveFile: vscode.window.activeTextEditor?.document.uri.fsPath
        });

        vscode.window.showInformationMessage(
            `LOCKEDIN restored ${path.basename(activeFile)} → line ${line}, column ${column}`
        );

    } catch (error) {
        writeStatus("error", error.message);

        vscode.window.showErrorMessage(
            `LOCKEDIN restore failed: ${error.message}`
        );
    }
}

function checkRestoreRequest() {
    if (!fs.existsSync(RESTORE_FILE)) {
        return;
    }

    try {
        const request = JSON.parse(
            fs.readFileSync(RESTORE_FILE, "utf8")
        );

        fs.unlinkSync(RESTORE_FILE);

        restoreContext(request);
    } catch (error) {
        writeStatus("error", error.message);
    }
}

function activate(context) {
    ensureRuntime();

    const inspectCommand = vscode.commands.registerCommand(
        "lockedin.inspectContext",
        () => {
            const current = getContext();
            writeJson(CONTEXT_FILE, current);

            const active = current.activeFile
                ? `File: ${current.activeFile}\nLine: ${current.line}\nColumn: ${current.column}`
                : "No active text editor.";

            vscode.window.showInformationMessage(
                `LOCKEDIN CONTEXT\n\n${active}`
            );
        }
    );

    context.subscriptions.push(inspectCommand);

    captureContext();

    const timer = setInterval(() => {
        captureContext();
        checkRestoreRequest();
    }, 500);

    context.subscriptions.push({
        dispose: () => clearInterval(timer)
    });
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};