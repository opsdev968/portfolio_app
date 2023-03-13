pipeline {              
    agent any
     environment { 
         AWS_REGION = 'eu-west-2'
         STAGING_SERVER_USERNAME = 'ubuntu' 
         STAGING_SERVER_IP = '52.31.114.218'
         IMG_NAME = 'todo'           
         
         COWSAY_CONTAINER_NAME = 'portfolio_app_app_todo_1'
         STAGING_SCRIPT = 'staging-k8s.sh'
         GIT_SSH_COMMAND = "ssh -o StrictHostKeyChecking=no"

     }
      //parameters {
      //booleanParam(name: 'SKIP_DEPLOY', defaultValue: false, description: 'SKIP_DEPLOY for feature branches')
      //booleanParam(name: 'SKIP_CLEANUP', defaultValue: false, description: 'SKIP_CLEANUP for feature branches')
      //}
    stages {
        stage('Init') {
        steps {
        script{
        if (env.BRANCH_NAME == "master")           {env.COW_FORWARDED_PORT = 80 }
         else if (env.BRANCH_NAME == "staging")    {env.COW_FORWARDED_PORT = 3000}
         else if ( env.BRANCH_NAME =~ "feature" )  {env.COW_FORWARDED_PORT = 3001  }          
         else {}
         }
        }
        }
     /// Enf of Var definitions

      stage('Git Clone') {
            steps {
                    //checkout scm 
                    //Git(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'olga-github', url: 'git@github.com:opsdev968/portfolio_app.git']])

                    git credentialsId: 'olga-github', url: 'git@github.com:opsdev968/portfolio_app.git'
                    
                }
        }
        stage('Build') {
            steps {
                script {
                    sh(returnStdout: true, script: 'git fetch --set-upstream origin main ') // --all
                    
                    def tagList = sh(returnStdout: true, script: 'git tag  --list --sort=-v:refname').trim().split('\n')
                    echo "Existing Git Tags: ${tagList}"
                    
         // Find the most advanced git tag and extract the minor version number
                    def lastTag = tagList[0]
                    def currentVersion = lastTag =~ /v(\d+)\.(\d+)/ ? "${RegExp.$1}.${RegExp.$2}" : "1.0"
                    echo "Current Version: ${currentVersion}"
                    
         // Increment the minor version number
                    def parts = currentVersion.tokenize('.')
                    def major = parts[0].toInteger()
                    def patch = parts[1].toInteger()
                    
                    patch += 1

                    echo "patch = ${patch}"
         // Construct the new version string
                    def newVersion = "${major}.${patch}"
                    echo "Next Version: ${newVersion}"
                    
        // Set the version number as an environment variable for use in following stages
                    env.VERSION = newVersion
                    echo "VERSION=${env.VERSION}"
        }
                echo 'Building..'                            
                sh "docker build -t todo.olgag:v${env.VERSION}  -t todo.olgag:latest ."        

                // Push the new tag to Git repository
                echo 'Git tag push New..' 
                sh "git tag v${env.VERSION}"

                echo 'Git tag push latest..' 

                sh "git push origin v${env.VERSION}"           
            }
        }
        stage('Local Test') {
            steps {
                echo 'Testing..'             
                sh "docker rm -f todo-olgag 2> /dev/null || true"
                //sh "docker run -d --rm -p $COWSAY_FORWARDED_PORT:8080 --network="host" --name cowsay-olgag cowsay:olgag.${env.BUILD_ID}  "   
                //sh "curl http://localhost:8686"
                // ??? sh 'docker run --rm --network="host" curlimages/curl curl http://localhost:8686'
                //sh "docker rm -f cowsay-olgag 2> /dev/null || true"
            }
        }
        stage('Publish') {
            steps {
                echo 'Publish..'  
                 withAWS(credentials:'aws-olgag',region:'eu-west-2') {    
                    sh "aws ecr get-login-password --region ${env.AWS_REGION} | docker login --username AWS --password-stdin 644435390668.dkr.ecr.${env.AWS_REGION}.amazonaws.com"          
                    sh "docker tag todo:olgag.${env.BUILD_ID} 644435390668.dkr.ecr.${env.AWS_REGION}.amazonaws.com/todo:olgag.${env.BUILD_ID} "
                    sh "docker push 644435390668.dkr.ecr.${env.AWS_REGION}.amazonaws.com/todo:olgag.${env.BUILD_ID}"
            }
            }
        }         
        stage('Deploy EC2') {
             when {
                    anyOf { branch 'master'                      
                            branch 'staging'
                             expression { branch 'feature/*'  && params.SKIP_DEPLOY == false }}
            }
            steps {
                echo 'Deploying....'
                script{
              
                   withCredentials([sshUserPrivateKey(credentialsId: "ck2-olga", keyFileVariable: 'keyfile')]) {                           
                      sh "scp -i ${keyfile} -o StrictHostKeyChecking=no  Deploy.sh ubuntu@52.31.114.218:Deploy.sh"
                      sh "ssh -i ${keyfile} ubuntu@52.31.114.218 -o StrictHostKeyChecking=no  ./Deploy.sh ${env.BUILD_ID} ${COW_FORWARDED_PORT} "                  
                 }
                }                          
            }
        }
        stage('test with curl EC2') {
        when {  anyOf {branch 'master' 
                       branch 'staging'
                       }
             }

            steps {
                  timeout(time: 5, unit: 'SECONDS') {  
                    retry(5) {
                            script{
                               sh "curl http://52.31.114.218:${COW_FORWARDED_PORT}"                           
                            }   
                    }
                  }
                }
        }
        stage('Cleanup') {            
            when {  branch 'feature/*'  }
            steps {     
                echo 'cleanup....'   
                script{
                    if (params.SKIP_CLEANUP == false && params.SKIP_DEPLOY == false)
                    {
                       withCredentials([sshUserPrivateKey(credentialsId: "ck2-olga", keyFileVariable: 'keyfile')]){         
                        sh "ssh -i ${keyfile} ubuntu@52.31.114.218 -o StrictHostKeyChecking=no  docker rm -f todo-olgag 2> /dev/null || true"
                        sh "ssh -i ${keyfile} ubuntu@52.31.114.218 -o StrictHostKeyChecking=no  docker rmi 644435390668.dkr.ecr.eu-west-1.amazonaws.com/todo:olgag.${env.BUILD_ID} 2> /dev/null || true"
                    }
                }               
            }
        }   
    }
    }
 //   post {
 //       always {
            
 //        withCredentials([sshUserPrivateKey(credentialsId: "ck2-olga", keyFileVariable: 'keyfile')]){         
 //               sh "ssh -i ${keyfile} ubuntu@52.31.114.218 -o StrictHostKeyChecking=no  docker rm -f cowsay-olgag 2> /dev/null || true"
//                sh "ssh -i ${keyfile} ubuntu@52.31.114.218 -o StrictHostKeyChecking=no  docker rmi 644435390668.dkr.ecr.eu-west-1.amazonaws.com/cowsay:olgag.${env.BUILD_ID} 2> /dev/null || true"
//
//            }        
//        }
//    }
}
