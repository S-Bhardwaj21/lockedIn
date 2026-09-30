package com.lockedin.worker

import android.os.Bundle
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtException
import ai.onnxruntime.OrtSession
import ai.onnxruntime.qnnpluginep.getEpName
import ai.onnxruntime.qnnpluginep.getLibraryPath
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.lockedin.worker.ui.theme.LockedInWorkerTheme
import org.json.JSONObject
import kotlin.math.sqrt

class MainActivity : ComponentActivity() {
    private var workerServer: WorkerServer? = null
    private var status = "Starting..."

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        status = try {
            runNpuInference()
        } catch (e: Exception) {
            e.printStackTrace()
            println("========================================")
            println("LOCKEDIN — NPU INFERENCE FAILURE")
            println("========================================")
            println("Exception: ${e.javaClass.name}")
            println("Message: ${e.message}")
            println("Cause: ${e.cause}")
            println("========================================")
            "INFERENCE ERROR:\n${e.javaClass.simpleName}\n${e.message}"
        }

        workerServer = WorkerServer(8765)
        workerServer?.start()

        setContent {
            LockedInWorkerTheme {
                WorkerStatus(status)
            }
        }
    }

    private fun runNpuInference(): String {
        val nativeLibDir = applicationInfo.nativeLibraryDir
        android.system.Os.setenv(
            "ADSP_LIBRARY_PATH",
            "$nativeLibDir:/vendor/lib/rfsa/adsp:/vendor/dsp/cdsp",
            true
        )
        println("LOCKEDIN ADSP_LIBRARY_PATH=$nativeLibDir")

        val environment = OrtEnvironment.getEnvironment()
        val epName = getEpName()
        val libraryPath = getLibraryPath()

        println("========================================")
        println("LOCKEDIN — QNN DIAGNOSTIC")
        println("========================================")
        println("QNN EP: $epName")
        println("QNN LIBRARY: $libraryPath")
        println("ADSP_LIBRARY_PATH=$nativeLibDir:/vendor/lib/rfsa/adsp:/vendor/dsp/cdsp")

        try {
            environment.registerExecutionProviderLibrary(
                epName,
                libraryPath
            )
            println("QNN EP registration: SUCCESS")
        } catch (e: OrtException) {
            if (e.message?.contains("already registered", ignoreCase = true) == true) {
                println("QNN EP registration: ALREADY REGISTERED")
            } else {
                throw e
            }
        }

        val qnnDevices = environment.getEpDevices().filter {
            it.epName == epName
        }

        if (qnnDevices.isEmpty()) {
            throw IllegalStateException("No QNN EP device found.")
        }

        println("QNN DEVICES:")
        qnnDevices.forEach { device ->
            println(device)
            println("  EP: ${device.epName}")
            println("  Vendor: ${device.device.vendor}")
            println("  Device type: ${device.device.type}")
        }

        val modelFile = copyAssetToInternalStorage("minilm_v2.onnx")
        val modelDataFile = copyAssetToInternalStorage("minilm_v2.data")
        val inputFile = copyAssetToInternalStorage("test_inputs.json")

        println("MODEL: ${modelFile.absolutePath}")
        println("MODEL SIZE: ${modelFile.length()} bytes")
        println("MODEL DATA SIZE: ${modelDataFile.length()} bytes")

        val inputJson = JSONObject(inputFile.readText())
        val goal = inputJson.getJSONObject("goal")
        val activity = inputJson.getJSONObject("activity")

        val sessionOptions = OrtSession.SessionOptions()

        sessionOptions.addConfigEntry(
            "session.disable_cpu_ep_fallback",
            "1"
        )

        println("CPU FALLBACK: DISABLED")
        println("QNN BACKEND: HTP")
        println("QNN SOC MODEL: 43 (SM8550)")
        println("QNN HTP ARCH: 73 (SM8550 / HTP v73)")
        println("Creating QNN session...")

        val qnnOptions = mapOf(
            "backend_type" to "htp",
            "soc_model" to "43",
            "htp_arch" to "73",
            "htp_performance_mode" to "burst",
            "htp_graph_finalization_optimization_mode" to "3",
            "enable_htp_fp16_precision" to "1",
            "offload_graph_io_quantization" to "0",
            "dump_json_qnn_graph" to "1"
        )

        sessionOptions.addExecutionProvider(
            qnnDevices,
            qnnOptions
        )

        val session = try {
            environment.createSession(
                modelFile.absolutePath,
                sessionOptions
            )
        } catch (e: OrtException) {
            println("========================================")
            println("QNN SESSION CREATION FAILED")
            println("========================================")
            println("ORT MESSAGE:")
            println(e.message)
            println("========================================")
            sessionOptions.close()
            throw e
        }

        println("========================================")
        println("QNN SESSION CREATED SUCCESSFULLY")
        println("========================================")

        val start = System.nanoTime()

        val goalEmbedding = runEmbedding(
            environment,
            session,
            goal.getJSONArray("input_ids"),
            goal.getJSONArray("attention_mask")
        )

        val activityEmbedding = runEmbedding(
            environment,
            session,
            activity.getJSONArray("input_ids"),
            activity.getJSONArray("attention_mask")
        )

        val elapsedMs = (System.nanoTime() - start) / 1_000_000.0

        session.close()
        sessionOptions.close()

        val alignment = cosineSimilarity(
            goalEmbedding,
            activityEmbedding
        )

        println("========================================")
        println("LOCKEDIN — REAL NPU INFERENCE")
        println("========================================")
        println("EP: $epName")
        println("Device: OnePlus 11 / SM8550")
        println("HTP: v73")
        println("Embedding dimensions: ${goalEmbedding.size}")
        println("Inference time: %.3f ms".format(elapsedMs))
        println("Alignment: %.6f".format(alignment))
        println("========================================")

        return """
            QNN NPU INFERENCE: SUCCESS
            
            EP: $epName
            
            OnePlus 11
            SM8550 / Snapdragon 8 Gen 2
            HTP v73
            
            Embedding: ${goalEmbedding.size}D
            
            Inference: %.3f ms
            
            Alignment:
            %.6f
        """.trimIndent().format(
            elapsedMs,
            alignment
        )
    }

    private fun runEmbedding(
        environment: OrtEnvironment,
        session: OrtSession,
        inputIdsJson: org.json.JSONArray,
        attentionMaskJson: org.json.JSONArray
    ): FloatArray {
        val inputIds = IntArray(inputIdsJson.length()) {
            inputIdsJson.getInt(it)
        }

        val attentionMask = IntArray(attentionMaskJson.length()) {
            attentionMaskJson.getInt(it)
        }

        val inputIdsTensor = OnnxTensor.createTensor(
            environment,
            arrayOf(inputIds)
        )

        val attentionMaskTensor = OnnxTensor.createTensor(
            environment,
            arrayOf(attentionMask)
        )

        val inputs = mapOf(
            "input_ids" to inputIdsTensor,
            "attention_mask" to attentionMaskTensor
        )

        val result = session.run(inputs)

        val output = result[0].value

        val embedding = when (output) {
            is Array<*> -> {
                val row = output[0]

                when (row) {
                    is ByteArray -> {
                        FloatArray(row.size) { i ->
                            ((row[i].toInt() and 0xFF) - 134) *
                                    0.0017485282151028514f
                        }
                    }

                    is UByteArray -> {
                        FloatArray(row.size) { i ->
                            (row[i].toInt() - 134) *
                                    0.0017485282151028514f
                        }
                    }

                    is FloatArray -> {
                        row
                    }

                    else -> {
                        throw IllegalStateException(
                            "Unexpected row output type: ${row?.javaClass}"
                        )
                    }
                }
            }

            else -> {
                throw IllegalStateException(
                    "Unexpected output type: ${output?.javaClass}"
                )
            }
        }

        result.close()
        inputIdsTensor.close()
        attentionMaskTensor.close()

        return embedding
    }

    private fun copyAssetToInternalStorage(name: String): java.io.File {
        val destination = java.io.File(filesDir, name)

        if (!destination.exists() || destination.length() == 0L) {
            assets.open(name).use { input ->
                destination.outputStream().use { output ->
                    input.copyTo(output)
                }
            }
        }

        return destination
    }

    private fun cosineSimilarity(
        a: FloatArray,
        b: FloatArray
    ): Float {
        if (a.size != b.size) {
            throw IllegalArgumentException(
                "Embedding dimensions differ: ${a.size} vs ${b.size}"
            )
        }

        var dot = 0.0
        var normA = 0.0
        var normB = 0.0

        for (i in a.indices) {
            dot += a[i].toDouble() * b[i].toDouble()
            normA += a[i].toDouble() * a[i].toDouble()
            normB += b[i].toDouble() * b[i].toDouble()
        }

        return (dot / (sqrt(normA) * sqrt(normB))).toFloat()
    }

    override fun onDestroy() {
        workerServer?.stop()
        workerServer = null
        super.onDestroy()
    }
}

@Composable
fun WorkerStatus(status: String) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text("LOCKEDIN AI WORKER")
        Text(status)
    }
}