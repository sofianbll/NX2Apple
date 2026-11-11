import SwiftUI
import NXCore
import NXModel
import NXLauncher

extension LauncherView {
    func configureBuild(_ game: LibraryGame) {
        guard !m.running else { page = .builds; return }
        if let folder = game.inputs[GameLibrary.folderInput]?.first {
            m.scan(folder: folder)   // a game folder is read again: its updates and DLC may have changed since
        } else {
            m.leaveGameFolder()
            for index in m.slots.indices {
                m.slots[index].paths = game.inputs[m.slots[index].id] ?? []
                m.slots[index].problem = ""
            }
            // The folder the game's files were found in (a base package may sit one level down in its own folder) — from the
            // scan, or from the last build. Falling back to the base's folder would put the update and DLC out of reach.
            m.gameDir = game.sourceFolder.isEmpty ? (m.basePath as NSString).deletingLastPathComponent : game.sourceFolder
        }
        m.macAppPath = game.appPath
        let modFolder = GameMod.folder(for: game, library: library.folder)
        let availableMods = GameMod.list(in: modFolder, titleID: game.titleID)
        m.modPaths = game.codeModsEnabled(availableMods) ? availableMods.filter(\.code).map(\.folder) : []
        let scanDefault = game.inputs[GameLibrary.folderInput] == nil ? (m.basePath as NSString).deletingLastPathComponent : m.gameDir
        m.outDir = BuildOutput.defaultDirectory(current: game.outputDirectory, scanDefault: scanDefault,
                                                sourceFolder: m.gameDir, gamesFolder: library.folder,
                                                remembered: game.outputDirectoryIsRemembered)
        m.done = false; m.doneNote = ""; m.stages = []
        m.target = game.lastTarget
        page = .builds
    }
}
