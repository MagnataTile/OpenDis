// domain/VpnBookHelper.kt
package com.magnatatitle.opendis.domain

import com.magnatatitle.opendis.model.VpnCredentials
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.util.concurrent.TimeUnit

object VpnBookHelper {

    private const val VPNBOOK_URL = "https://www.vpnbook.com/pt/freevpn/openvpn"
    private const val VPNBOOK_API_URL = "https://www.vpnbook.com/api/openvpn"

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    data class VpnBookResult(
        val profileFile: File,
        val credentials: VpnCredentials
    )

    suspend fun fetchCredentials(): VpnCredentials? = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url(VPNBOOK_URL)
                .header("User-Agent", "Mozilla/5.0 (Linux; Android 14)")
                .build()

            val response = client.newCall(request).execute()
            val html = response.body?.string() ?: return@withContext null

            // Regex para capturar a senha — igual ao seu código Windows
            val passwordPattern = Regex(
                """(?:Senha|Password).{0,500}?<code[^>]*>\s*([^<\s]+)\s*</code>""",
                setOf(RegexOption.IGNORE_CASE, RegexOption.DOT_MATCHES_ALL)
            )

            val password = passwordPattern.find(html)?.groupValues?.getOrNull(1)
                ?: return@withContext null

            VpnCredentials(
                username = "vpnbook",
                password = password
            )
        } catch (e: Exception) {
            null
        }
    }

    suspend fun downloadProfile(
        vpnDir: File,
        server: String = "us16.vpnbook.com",
        protocol: String = "tcp80"
    ): File? = withContext(Dispatchers.IO) {
        try {
            val url = "$VPNBOOK_API_URL?hostname=$server&protocol=$protocol"

            val request = Request.Builder()
                .url(url)
                .header("User-Agent", "Mozilla/5.0 (Linux; Android 14)")
                .build()

            val response = client.newCall(request).execute()
            val body = response.body?.bytes() ?: return@withContext null

            val filename = "vpnbook-$server-$protocol.ovpn"
            val outputFile = File(vpnDir, filename)
            outputFile.writeBytes(body)

            if (outputFile.exists() && outputFile.length() > 100) outputFile else null
        } catch (e: Exception) {
            null
        }
    }
}
