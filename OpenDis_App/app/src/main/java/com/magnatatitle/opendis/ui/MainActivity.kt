package com.magnatatitle.opendis.ui

import android.Manifest
import android.content.pm.PackageManager
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.magnatatitle.opendis.ui.navigation.OpenDisNavGraph
import com.magnatatitle.opendis.ui.theme.OpenDisTheme
import com.magnatatitle.opendis.viewmodel.OpenDisViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    private val viewModel: OpenDisViewModel by viewModels()

    /**
     * Launcher for notification permission (Android 13+)
     */
    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        Log.d("OpenDis/Main", "Notification permission granted: $granted")
    }

    /**
     * Android VPN authorization result.
     */
    private val vpnPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val granted = result.resultCode == RESULT_OK
        Log.d("OpenDis/Main", "VPN Permission result: $granted")
        viewModel.onVpnPermissionResult(granted)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d("OpenDis/Main", "onCreate")

        // 1. Request notification permission if needed
        requestNotificationPermission()

        // 2. We DO NOT request VPN permission on startup anymore to avoid double prompts.
        // It will be requested only when the user clicks "Start" or enters a profile that needs it,
        // and only if VpnService.prepare(this) returns an Intent.

        // 3. UI
        setContent {
            OpenDisTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    OpenDisNavGraph(
                        onRequestVpnPermission = {
                            requestVpnPermission()
                        }
                    )
                }
            }
        }
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
                PackageManager.PERMISSION_GRANTED) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    /**
     * Called by the UI/ViewModel when VPN authorization is actually required.
     */
    private fun requestVpnPermission() {
        val intent = VpnService.prepare(this)
        if (intent != null) {
            Log.d("OpenDis/Main", "Requesting VPN authorization from user...")
            vpnPermissionLauncher.launch(intent)
        } else {
            Log.d("OpenDis/Main", "VPN already authorized by system.")
            viewModel.setVpnAuthorized()
        }
    }
}
