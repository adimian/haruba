var require = {
    baseUrl: "js",
    paths: {
        "jquery": "https://cdnjs.cloudflare.com/ajax/libs/jquery/2.2.3/jquery.min",
        "bootstrap": "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min",
        "director": "https://cdnjs.cloudflare.com/ajax/libs/Director/1.2.8/director.min",
        "ko": "https://cdnjs.cloudflare.com/ajax/libs/knockout/3.4.0/knockout-min",
        "text": "https://cdnjs.cloudflare.com/ajax/libs/require-text/2.0.12/text.min",
        "noty": "https://cdnjs.cloudflare.com/ajax/libs/jquery-noty/2.3.8/packaged/jquery.noty.packaged",
        "cookies-js": "https://cdnjs.cloudflare.com/ajax/libs/Cookies.js/1.2.1/cookies.min",
        "dropzone": "https://cdnjs.cloudflare.com/ajax/libs/dropzone/4.3.0/min/dropzone-amd-module.min"
    },
    shim: {
        "bootstrap": {
            deps: ["jquery"]
        },
        "noty": {
            deps: ["jquery"]
        },
        "cookies-js": {
            deps: ["jquery"]
        }
    }
};
