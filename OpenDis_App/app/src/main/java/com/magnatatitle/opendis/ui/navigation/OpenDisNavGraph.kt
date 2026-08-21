// ui/navigation/OpenDisNavGraph.kt
package com.magnatatitle.opendis.ui.navigation

import androidx.compose.runtime.Composable
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.magnatatitle.opendis.ui.screens.*
import com.magnatatitle.opendis.viewmodel.OpenDisViewModel

object Routes {
    const val SPLASH = "splash"
    const val PROFILE_SELECTION = "profile_selection"
    const val CREDENTIALS = "credentials"
    const val CONNECTION = "connection"
    const val COMPLETED = "completed"
}

@Composable
fun OpenDisNavGraph(
    onRequestVpnPermission: () -> Unit,
    viewModel: OpenDisViewModel = hiltViewModel()
) {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = Routes.SPLASH
    ) {
        composable(Routes.SPLASH) {
            SplashScreen(
                viewModel = viewModel,
                onReady = {
                    navController.navigate(Routes.PROFILE_SELECTION) {
                        popUpTo(Routes.SPLASH) { inclusive = true }
                    }
                }
            )
        }

        composable(Routes.PROFILE_SELECTION) {
            ProfileSelectionScreen(
                viewModel = viewModel,
                onProfileSelected = {
                    val profile = viewModel.selectedProfile.value
                    if (profile != null) {
                        // Se o perfil exige auth mas já temos credenciais salvas, pulamos para a conexão
                        if (profile.requiresAuth && viewModel.savedCredentials.value == null) {
                            navController.navigate(Routes.CREDENTIALS)
                        } else {
                            navController.navigate(Routes.CONNECTION)
                        }
                    }
                },
                onRandomVpn = {
                    viewModel.startVpnBookRandom()
                    navController.navigate(Routes.CONNECTION)
                }
            )
        }

        composable(Routes.CREDENTIALS) {
            CredentialsScreen(
                viewModel = viewModel,
                onContinue = {
                    navController.navigate(Routes.CONNECTION)
                },
                onBack = { navController.popBackStack() }
            )
        }

        composable(Routes.CONNECTION) {
            ConnectionScreen(
                viewModel = viewModel,
                onRequestVpnPermission = onRequestVpnPermission,
                onCompleted = {
                    navController.navigate(Routes.COMPLETED) {
                        popUpTo(Routes.CONNECTION) { inclusive = true }
                    }
                },
                onBack = {
                    viewModel.disconnectVpn()
                    viewModel.reset()
                    navController.popBackStack()
                }
            )
        }

        composable(Routes.COMPLETED) {
            CompletedScreen(
                viewModel = viewModel,
                onFinish = { 
                    viewModel.reset()
                    navController.navigate(Routes.PROFILE_SELECTION) {
                        popUpTo(Routes.COMPLETED) { inclusive = true }
                    }
                }
            )
        }
    }
}
