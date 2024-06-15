def APP_NAME = "webchela"
def APP_REPO = "https://github.com/livelace/webchela.git"
def APP_VERSION = env.VERSION + '-${GIT_COMMIT_SHORT}'
def IMAGE_TAG = env.VERSION == "master" ? "latest" : env.VERSION

libraries {
    //dependency_check
    //dependency_track {
    //    project = "${APP_NAME}"
    //    version = env.VERSION
    //}
    git {
        repo_url = "${APP_REPO}"
        repo_branch = env.VERSION
    }
    //harbor_replicate {
    //    policy = "${APP_NAME}"
    //}
    k8s_build {
        image = "registry.livelace.ru/dev/webchela:${IMAGE_TAG}"
    }
    kaniko {
        destination = "infra/${APP_NAME}:${IMAGE_TAG}"
    }
    mattermost
    //nexus {
    //   source = "dist/webchela-1.7.0-py3.8.egg"
    //   destination = "dists-internal/${APP_NAME}/${APP_NAME}-${APP_VERSION}.egg"

    //}
    python
    //sonarqube
}
