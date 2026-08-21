package com.magnatatitle.opendis.vpn

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.magnatatitle.opendis.R
import com.magnatatitle.opendis.ui.MainActivity
class OpenDisNotification(
    private val service: Service,
    private val notificationManager: NotificationManager
) {

    companion object {
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "opendis_vpn"
    }

    init {
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "OpenDis VPN",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Status da conexão VPN do OpenDis"
            }
            notificationManager.createNotificationChannel(channel)
        }
    }

    fun withTimer(): Boolean = false

    fun start() {
        val notification = createNotification("Iniciando VPN...")
        service.startForeground(NOTIFICATION_ID, notification)
    }

    fun stop() {
        service.stopForeground(Service.STOP_FOREGROUND_REMOVE)
    }

    fun createNotification(description: String): Notification {
        val intent = Intent(service, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
            service,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(service, CHANNEL_ID)
            .setContentTitle("OpenDis VPN")
            .setContentText(description)
            .setSmallIcon(R.drawable.ic_vpn)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    fun updateNotification(notification: Notification) {
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
}
