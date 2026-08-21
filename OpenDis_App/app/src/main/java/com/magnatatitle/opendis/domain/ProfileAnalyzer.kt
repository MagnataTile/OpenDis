// domain/ProfileAnalyzer.kt
package com.magnatatitle.opendis.domain

import java.io.File
import java.security.MessageDigest

object ProfileAnalyzer {

    fun requiresCredentials(profileFile: File): Boolean {
        val content = profileFile.readText(Charsets.UTF_8)
        
        // Verifica tags XML do OpenVPN 3
        if (content.contains("<auth-user-pass>", ignoreCase = true)) return true

        return content.lines().any { line ->
            val trimmed = line.trim()
            if (trimmed.startsWith("#") || trimmed.startsWith(";")) return@any false
            
            val lower = trimmed.lowercase()
            if (lower.startsWith("auth-user-pass")) {
                val parts = trimmed.split("\\s+".toRegex())
                // Se for apenas "auth-user-pass", requer entrada. 
                // Se tiver caminho, requer entrada apenas se o arquivo não existir.
                return@any parts.size == 1 || !File(profileFile.parentFile, parts[1]).exists()
            }
            false
        }
    }

    fun computeHash(profileFile: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        // Normalizamos os line endings para o hash ser consistente mesmo se o arquivo mudar de \r\n para \n
        val normalizedContent = profileFile.readText().replace("\r\n", "\n")
        val bytes = normalizedContent.toByteArray(Charsets.UTF_8)
        return digest.digest(bytes).joinToString("") { "%02x".format(it) }
    }

    fun extractServerInfo(profileFile: File): Pair<String?, String?> {
        var server: String? = null
        var protocol: String? = null

        profileFile.readLines().forEach { line ->
            val trimmed = line.trim()
            if (trimmed.lowercase().startsWith("remote ")) {
                val parts = trimmed.split("\\s+".toRegex())
                if (parts.size >= 2) server = parts[1]
            }
            if (trimmed.lowercase().startsWith("proto ")) {
                val parts = trimmed.split("\\s+".toRegex())
                if (parts.size >= 2) protocol = parts[1]
            }
        }
        return server to protocol
    }
}
