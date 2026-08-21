package com.magnatatitle.opendis.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.magnatatitle.opendis.model.VpnConnectionState
import com.magnatatitle.opendis.viewmodel.OpenDisViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConnectionScreen(
    viewModel: OpenDisViewModel,
    onRequestVpnPermission: () -> Unit,
    onCompleted: () -> Unit,
    onBack: () -> Unit
) {
    val logs by viewModel.logs.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()
    val isVpnAuthorized by viewModel.isVpnAuthorized.collectAsState()
    val currentIp by viewModel.currentIp.collectAsState()

    val listState = rememberLazyListState()
    var isRunning by remember { mutableStateOf(false) }

    // Auto-scroll para o último log
    LaunchedEffect(logs.size) {
        if (logs.isNotEmpty()) {
            listState.animateScrollToItem(logs.size - 1)
        }
    }

    // Monitorar conclusão
    LaunchedEffect(connectionState) {
        if (connectionState is VpnConnectionState.Completed) {
            onCompleted()
        }
    }

    fun handleStartClick() {
        if (!isVpnAuthorized) {
            onRequestVpnPermission()
        } else {
            isRunning = true
            viewModel.startFullFlow()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text("🚀 Fluxo de Operação", fontWeight = FontWeight.Bold)
                },
                navigationIcon = {
                    if (!isRunning) {
                        IconButton(onClick = onBack) {
                            Icon(Icons.Default.ArrowBack, contentDescription = "Voltar")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF1e1e2e),
                    titleContentColor = Color.White,
                    navigationIconContentColor = Color.White
                )
            )
        },
        containerColor = Color(0xFF1e1e2e)
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(Modifier.height(12.dp))

            // ─── Passos do Fluxo ───
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF2f3136)
                )
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("Status do Processo:", fontWeight = FontWeight.Bold, color = Color(0xFFa0a0b0), fontSize = 12.sp)
                    Spacer(Modifier.height(4.dp))
                    
                    val steps = listOf(
                        "1 - Inicialização e Ambiente",
                        "2 - Estabelecimento da VPN",
                        "3 - Validação de Rede e IP",
                        "4 - Execução do Discord",
                        "5 - Finalização"
                    )

                    steps.forEachIndexed { index, s ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            val isCurrent = isRunning && when(index) {
                                0 -> connectionState is VpnConnectionState.Disconnected
                                1 -> connectionState is VpnConnectionState.Connecting
                                2 -> connectionState is VpnConnectionState.Connecting && logs.any { it.contains("⏳") }
                                3 -> connectionState is VpnConnectionState.Connected
                                4 -> connectionState is VpnConnectionState.Completed
                                else -> false
                            }
                            
                            val isDone = connectionState is VpnConnectionState.Completed || (isRunning && when(index) {
                                0 -> connectionState !is VpnConnectionState.Disconnected
                                1 -> connectionState is VpnConnectionState.Connected || connectionState is VpnConnectionState.Completed
                                2 -> connectionState is VpnConnectionState.Connected || connectionState is VpnConnectionState.Completed
                                3 -> connectionState is VpnConnectionState.Completed
                                else -> false
                            })

                            Icon(
                                if (isDone) Icons.Default.CheckCircle
                                else if (isCurrent) Icons.Default.PlayArrow
                                else Icons.Default.RadioButtonUnchecked,
                                contentDescription = null,
                                tint = when {
                                    isDone -> Color(0xFF57F287)
                                    isCurrent -> Color(0xFF5865F2)
                                    else -> Color(0xFF404040)
                                },
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(Modifier.width(6.dp))
                            Text(
                                s,
                                color = when {
                                    isDone -> Color(0xFF57F287)
                                    isCurrent -> Color.White
                                    else -> Color(0xFF666675)
                                },
                                fontSize = 12.sp
                            )
                        }
                    }
                }
            }

            Spacer(Modifier.height(8.dp))

            // ─── IP Atual ───
            if (currentIp != null) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF2f3136)
                    )
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.Language, contentDescription = null, tint = Color(0xFFa0a0b0))
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "IP Público: ${currentIp}",
                            color = Color(0xFFa0a0b0),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            }

            Spacer(Modifier.height(8.dp))

            // ─── Logs de Sistema ───
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF12121a)
                ),
                shape = RoundedCornerShape(8.dp)
            ) {
                LazyColumn(
                    state = listState,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(8.dp)
                ) {
                    items(logs) { log ->
                        val isError = log.contains("❌") || log.contains("Erro")
                        val isWarning = log.contains("⚠️")
                        val isSuccess = log.contains("✅") || log.contains("🎉")
                        
                        Text(
                            text = log,
                            color = when {
                                isError -> Color(0xFFed4245)
                                isWarning -> Color(0xFFFAA61A)
                                isSuccess -> Color(0xFF57F287)
                                else -> Color(0xFF8e9297)
                            },
                            fontSize = 11.sp,
                            fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace,
                            modifier = Modifier.padding(vertical = 1.dp)
                        )
                    }
                }
            }

            Spacer(Modifier.height(12.dp))

            // ─── Estado Atual ───
            Text(
                when (connectionState) {
                    is VpnConnectionState.Disconnected -> "Pronto para Iniciar"
                    is VpnConnectionState.Connecting -> "Sincronizando Rede..."
                    is VpnConnectionState.Connected -> "Túnel VPN Estabelecido"
                    is VpnConnectionState.Error -> "Falha Detectada"
                    is VpnConnectionState.Completed -> "PROCESSO FINALIZADO"
                },
                color = when (connectionState) {
                    is VpnConnectionState.Connected -> Color(0xFF57F287)
                    is VpnConnectionState.Error -> Color(0xFFed4245)
                    is VpnConnectionState.Completed -> Color(0xFF57F287)
                    else -> Color(0xFFa0a0b0)
                },
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp
            )

            Spacer(Modifier.height(12.dp))

            // ─── Botões de Ação ───
            if (!isRunning && connectionState !is VpnConnectionState.Completed) {
                Button(
                    onClick = { handleStartClick() },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isVpnAuthorized) Color(0xFF5865F2) else Color(0xFFFAA61A)
                    ),
                    shape = RoundedCornerShape(26.dp)
                ) {
                    Icon(
                        if (isVpnAuthorized) Icons.Default.PlayArrow else Icons.Default.Security, 
                        contentDescription = null
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        if (isVpnAuthorized) "INICIAR PROCESSO" else "AUTORIZAR REDE", 
                        fontWeight = FontWeight.Bold, 
                        fontSize = 16.sp
                    )
                }

                Spacer(Modifier.height(8.dp))

                TextButton(
                    onClick = onBack,
                    modifier = Modifier.height(40.dp)
                ) {
                    Text("VOLTAR", color = Color(0xFF888888), fontWeight = FontWeight.Bold)
                }
            }

            if (isRunning && connectionState !is VpnConnectionState.Completed && connectionState !is VpnConnectionState.Error) {
                LinearProgressIndicator(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(4.dp),
                    color = Color(0xFF5865F2),
                    trackColor = Color(0xFF404040)
                )
            } else if (connectionState is VpnConnectionState.Error) {
                Button(
                    onClick = { 
                        isRunning = false
                        viewModel.reset()
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFed4245))
                ) {
                    Text("Tentar Novamente")
                }
            }

            Spacer(Modifier.height(8.dp))
        }
    }
}
