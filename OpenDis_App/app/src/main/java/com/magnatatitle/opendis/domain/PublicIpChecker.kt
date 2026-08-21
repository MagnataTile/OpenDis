// domain/PublicIpChecker.kt
package com.magnatatitle.opendis.domain

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

object PublicIpChecker {

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    suspend fun getCurrentIp(): String? = withContext(Dispatchers.IO) {
        val services = listOf(
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://checkip.amazonaws.com",
            "https://icanhazip.com"
        )

        for (url in services) {
            // Tenta cada serviço até 2 vezes
            repeat(2) {
                try {
                    val request = Request.Builder()
                        .url(url)
                        .header("User-Agent", "Mozilla/5.0")
                        .build()

                    val response = client.newCall(request).execute()
                    val ip = response.body?.string()?.trim()

                    if (!ip.isNullOrEmpty() && ip.matches(Regex("^[0-9a-fA-F:.]+$"))) {
                        return@withContext ip
                    }
                } catch (_: Exception) { }
            }
        }
        null
    }
}
