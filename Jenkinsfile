pipeline {
    agent { label 'windows' }

    triggers {
        githubPush()
    }

    parameters {
        booleanParam(name: 'RUN_ANDROID_REAL', defaultValue: false, description: 'Run the Android real-device lane')
        booleanParam(name: 'RUN_ANDROID_EMULATOR', defaultValue: false, description: 'Run the Windows Android Studio emulator lane')
        booleanParam(name: 'RUN_ANDROID_MONKEY', defaultValue: false, description: 'Run the controlled Android Monkey stability lane')
        booleanParam(name: 'CONFIRM_ANDROID_MONKEY_ISOLATED_ENV', defaultValue: false, description: 'Confirm Monkey uses an isolated test account and environment')
        choice(name: 'ANDROID_MONKEY_TARGET', choices: ['emulator', 'real'], description: 'Windows device pool used by the Monkey lane')
        string(name: 'ANDROID_APK_SOURCE', defaultValue: '', description: 'Direct APK URL or path visible to each agent')
        string(name: 'ANDROID_REAL_UDIDS', defaultValue: '', description: 'Comma-separated ADB serials for real devices')
        string(name: 'ANDROID_AVD_NAME', defaultValue: '', description: 'AVD installed on the Windows Android agent')
        string(name: 'ANDROID_EMULATOR_PORT', defaultValue: '5554', description: 'Even emulator console port')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Environment') {
            steps {
                powershell '.\\setup-ci.ps1'
            }
        }

        stage('Quality Gate') {
            steps {
                bat 'call platform.cmd ci'
            }
        }

        stage('Configured Test CLIs') {
            when {
                expression { return env.AUTOTEST_CI_TOOLS_CONFIG?.trim() }
            }
            steps {
                bat 'call platform.cmd ci-tools -ConfigPath "%AUTOTEST_CI_TOOLS_CONFIG%"'
            }
        }

        stage('Android Real Device') {
            when {
                expression { return params.RUN_ANDROID_REAL }
            }
            steps {
                powershell '.\\setup-mobile.ps1 -SkipCiSetup'
                script {
                    def apkSource = params.ANDROID_APK_SOURCE?.trim() ?: env.AUTOTEST_ANDROID_APK_SOURCE?.trim()
                    if (!apkSource) {
                        error('ANDROID_APK_SOURCE or AUTOTEST_ANDROID_APK_SOURCE is required')
                    }
                    def realDevices = params.ANDROID_REAL_UDIDS?.split(',')?.collect { it.trim() }?.findAll { it }
                    if (!realDevices) {
                        error('ANDROID_REAL_UDIDS is required for unattended real-device execution')
                    }
                    withEnv([
                        "AUTOTEST_ANDROID_APK_SOURCE=${apkSource}",
                        "AUTOTEST_MOBILE_DEVICES=${groovy.json.JsonOutput.toJson(realDevices)}",
                        "AUTOTEST_MOBILE_CONFIG=config/mobile-ci.soulfree.yaml"
                    ]) {
                        bat '".venv\\Scripts\\python.exe" scripts\\prepare_android_apk.py --output-root artifacts\\mobile-ci'
                        env.AUTOTEST_ANDROID_APP = readFile('artifacts/mobile-ci/current-apk.path').trim()
                        env.AUTOTEST_ANDROID_APK_METADATA = readFile('artifacts/mobile-ci/current-apk-metadata.path').trim()
                        bat 'call platform.cmd mobile-ci -ConfigPath config\\mobile-ci.soulfree.yaml'
                    }
                }
            }
        }

        stage('Android Windows Emulator') {
            agent { label 'windows' }
            when {
                beforeAgent true
                expression { return params.RUN_ANDROID_EMULATOR }
            }
            steps {
                checkout scm
                powershell '.\\setup-mobile.ps1 -SkipCiSetup'
                script {
                    def apkSource = params.ANDROID_APK_SOURCE?.trim() ?: env.AUTOTEST_ANDROID_APK_SOURCE?.trim()
                    if (!apkSource) {
                        error('ANDROID_APK_SOURCE or AUTOTEST_ANDROID_APK_SOURCE is required')
                    }
                    if (!params.ANDROID_AVD_NAME?.trim()) {
                        error('ANDROID_AVD_NAME is required for the Windows emulator lane')
                    }
                    def emulatorPort = params.ANDROID_EMULATOR_PORT.trim()
                    def emulatorUdid = "emulator-${emulatorPort}"
                    withEnv([
                        "AUTOTEST_ANDROID_APK_SOURCE=${apkSource}",
                        "AUTOTEST_MOBILE_DEVICES=${groovy.json.JsonOutput.toJson([emulatorUdid])}",
                        "AUTOTEST_MOBILE_CONFIG=config/mobile-ci.emulator.yaml"
                    ]) {
                        bat '".venv\\Scripts\\python.exe" scripts\\prepare_android_apk.py --output-root artifacts\\mobile-ci'
                        env.AUTOTEST_ANDROID_APP = readFile('artifacts/mobile-ci/current-apk.path').trim()
                        env.AUTOTEST_ANDROID_APK_METADATA = readFile('artifacts/mobile-ci/current-apk-metadata.path').trim()
                        try {
                            bat "\".venv\\Scripts\\python.exe\" scripts\\manage_android_emulator.py start --avd \"${params.ANDROID_AVD_NAME.trim()}\" --port ${emulatorPort} --state artifacts\\mobile-ci\\emulator-state.json"
                            bat 'call platform.cmd mobile-ci -ConfigPath config\\mobile-ci.emulator.yaml'
                        } finally {
                            bat '".venv\\Scripts\\python.exe" scripts\\manage_android_emulator.py stop --state artifacts\\mobile-ci\\emulator-state.json || exit /b 0'
                        }
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/mobile-ci/**/*,artifacts/mobile-ci/**/*', allowEmptyArchive: true
                    junit testResults: 'reports/mobile-ci/**/pytest-junit.xml', allowEmptyResults: true
                }
            }
        }

        stage('Android Monkey Stability') {
            when {
                expression { return params.RUN_ANDROID_MONKEY }
            }
            steps {
                powershell '.\\setup-mobile.ps1 -SkipCiSetup'
                script {
                    if (!params.CONFIRM_ANDROID_MONKEY_ISOLATED_ENV) {
                        error('Monkey requires CONFIRM_ANDROID_MONKEY_ISOLATED_ENV=true')
                    }
                    def apkSource = params.ANDROID_APK_SOURCE?.trim() ?: env.AUTOTEST_ANDROID_APK_SOURCE?.trim()
                    if (!apkSource) {
                        error('ANDROID_APK_SOURCE or AUTOTEST_ANDROID_APK_SOURCE is required')
                    }

                    def target = params.ANDROID_MONKEY_TARGET?.trim()?.toLowerCase() ?: 'emulator'
                    def configPath = ''
                    def monkeyDevices = []
                    def startEmulator = false
                    def emulatorPort = params.ANDROID_EMULATOR_PORT.trim()

                    if (target == 'real') {
                        monkeyDevices = params.ANDROID_REAL_UDIDS?.split(',')?.collect { it.trim() }?.findAll { it }
                        if (!monkeyDevices) {
                            error('ANDROID_REAL_UDIDS is required when ANDROID_MONKEY_TARGET=real')
                        }
                        configPath = 'config\\mobile-ci.soulfree.yaml'
                    } else if (target == 'emulator') {
                        if (!params.ANDROID_AVD_NAME?.trim()) {
                            error('ANDROID_AVD_NAME is required when ANDROID_MONKEY_TARGET=emulator')
                        }
                        monkeyDevices = ["emulator-${emulatorPort}"]
                        configPath = 'config\\mobile-ci.emulator.yaml'
                        startEmulator = true
                    } else {
                        error("Unsupported ANDROID_MONKEY_TARGET: ${target}")
                    }

                    withEnv([
                        "AUTOTEST_ANDROID_APK_SOURCE=${apkSource}",
                        "AUTOTEST_MOBILE_DEVICES=${groovy.json.JsonOutput.toJson(monkeyDevices)}",
                        "AUTOTEST_MOBILE_SCENARIOS=${groovy.json.JsonOutput.toJson(['android-monkey-stability'])}",
                        "AUTOTEST_MOBILE_CONFIG=${configPath}",
                        'AUTOTEST_ALLOW_MUTATIONS=true',
                        'AUTOTEST_ALLOW_HIGH_RISK=true',
                        'AUTOTEST_MOBILE_ALLOW_MONKEY=true'
                    ]) {
                        bat '".venv\\Scripts\\python.exe" scripts\\prepare_android_apk.py --output-root artifacts\\mobile-ci'
                        env.AUTOTEST_ANDROID_APP = readFile('artifacts/mobile-ci/current-apk.path').trim()
                        env.AUTOTEST_ANDROID_APK_METADATA = readFile('artifacts/mobile-ci/current-apk-metadata.path').trim()
                        if (startEmulator) {
                            try {
                                bat "\".venv\\Scripts\\python.exe\" scripts\\manage_android_emulator.py start --avd \"${params.ANDROID_AVD_NAME.trim()}\" --port ${emulatorPort} --state artifacts\\mobile-ci\\monkey-emulator-state.json"
                                bat "call platform.cmd mobile-ci -ConfigPath ${configPath}"
                            } finally {
                                bat '".venv\\Scripts\\python.exe" scripts\\manage_android_emulator.py stop --state artifacts\\mobile-ci\\monkey-emulator-state.json || exit /b 0'
                            }
                        } else {
                            bat "call platform.cmd mobile-ci -ConfigPath ${configPath}"
                        }
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/mobile-ci/**/*,artifacts/mobile-ci/**/*', allowEmptyArchive: true
                    junit testResults: 'reports/mobile-ci/**/pytest-junit.xml', allowEmptyResults: true
                }
            }
        }

    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/ci/**/*,reports/ci-tools/**/*,reports/mobile-ci/**/*,artifacts/mobile-ci/**/*', allowEmptyArchive: true
            junit testResults: 'reports/ci/**/*-junit.xml,reports/ci-tools/**/*-junit.xml,reports/mobile-ci/**/pytest-junit.xml', allowEmptyResults: true
        }
    }
}
