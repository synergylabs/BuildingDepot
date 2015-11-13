(function() {
    var app = angular.module('myApp', []);

    app.config(['$interpolateProvider', function($interpolateProvider) {
      $interpolateProvider.startSymbol('{[');
      $interpolateProvider.endSymbol(']}');
    }]);

    app.controller = ('metadataController', function($scope, $http) {
        $scope.ctl.select = function(name) {
            this.selected = name;
        };
    });
})();