app.controller('KanbanCtrl', function ($scope, $http) {
	$scope.api = '/api';
	
	$scope.steps = [];
	$scope.priorities = [
		{'id' : 'yellow', 'value' : 'Baixa'},
		{'id' : 'red', 'value' : 'Alta'}
	]

	$scope.update_kanban=function() {
		$http.get("/api/steps")
		    .success(function(data) { 
		        $scope.steps = data.steps;
				//console.log($scope.steps);
			});
	}

	$scope.socket = io.connect('http://' + document.domain + ':' + location.port + '/update_steps');
	$scope.socket.on('update_all_clients', function() {
		$scope.update_kanban();
	});

	$scope.call_socket=function(){
		$scope.socket.emit('broadcast update');
	}

	$scope.update_kanban();
	$scope.call_socket();

	$scope.onDropStep=function(data,evt,step){
		$http.get($scope.api + '/tasks/' + data.id + '/' + step.id)
			.success(function(data) {
	            $scope.steps = data.steps;
	            $scope.call_socket();
	    	});
	}
	
	$scope.removeTask = function(task) {
		$http.delete($scope.api + '/tasks/' + task.id)
			.success(function(data) {
	            if(data.result)
	            	$scope.call_socket();
	    	});
	}

	$scope.popularDados=function(){
		$http.get('/db/populate')
			.success(function() {
	            $scope.call_socket();
	    	});
	}
	
	$scope.saveTask = function(task) {
		if(!!task.id) {
			$http.put($scope.api + '/tasks/' + task.id, $scope.domain)
				.success(function() {
		            $scope.call_socket();
		            $scope.modalShown = false;
		    	});					
		} else {
			$http.post($scope.api + '/tasks', $scope.domain)
				.success(function() {
		            $scope.call_socket();
		            $scope.modalShown = false;
		    	});
		}
	}

	$scope.modalShown = false;
	$scope.addTask = function(step_id) {
		$scope.modalShown = !$scope.modalShown;
		$scope.domain = {};
		$scope.domain.stepId = step_id;
		$scope.domain.id=undefined;
		$scope.domain.color='yellow';
	};
	
	$scope.editTask = function(task) {
		$scope.domain = angular.copy(task);
		delete $scope.domain._id;
		$scope.modalShown = true;
	}
});
