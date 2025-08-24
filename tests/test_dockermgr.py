from unittest.mock import Mock, patch

from pman.dockermgr import DockerManager


class TestDockerManager:
    """Test cases for DockerManager class."""

    def test_docker_networks_single_network(self):
        """Test that a single network is correctly configured."""
        config = {'DOCKER_NETWORKS': ['test-network']}
        mock_docker_client = Mock()

        with patch('docker.from_env', return_value=mock_docker_client):
            manager = DockerManager(config, mock_docker_client)

        # Mock the containers.run method
        mock_container = Mock()
        mock_docker_client.containers.run.return_value = mock_container

        # Test parameters
        image = 'test-image'
        command = ['test', 'command']
        name = 'test-job'
        resources_dict = {'number_of_workers': 1, 'cpu_limit': 1, 'memory_limit': 100, 'gpu_limit': 0}
        env = []
        uid = None
        gid = None
        mounts_dict = {
            'inputdir_source': '/input',
            'inputdir_target': '/share/incoming',
            'outputdir_source': '/output',
            'outputdir_target': '/share/outgoing'
        }

        # Call schedule_job
        result = manager.schedule_job(image, command, name, resources_dict, env, uid, gid, mounts_dict)

        # Verify that containers.run was called with the correct network parameter
        mock_docker_client.containers.run.assert_called_once()
        call_args = mock_docker_client.containers.run.call_args
        assert call_args[1]['network'] == 'test-network'
        assert result == mock_container

    def test_docker_networks_multiple_networks(self):
        """Test that multiple networks are correctly configured."""
        config = {'DOCKER_NETWORKS': ['network1', 'network2']}
        mock_docker_client = Mock()

        with patch('docker.from_env', return_value=mock_docker_client):
            manager = DockerManager(config, mock_docker_client)

        # Mock the containers.run method
        mock_container = Mock()
        mock_docker_client.containers.run.return_value = mock_container

        # Mock the networks.get method and network.connect method for additional networks
        mock_network = Mock()
        mock_docker_client.networks.get.return_value = mock_network

        # Test parameters
        image = 'test-image'
        command = ['test', 'command']
        name = 'test-job'
        resources_dict = {'number_of_workers': 1, 'cpu_limit': 1, 'memory_limit': 100, 'gpu_limit': 0}
        env = []
        uid = None
        gid = None
        mounts_dict = {
            'inputdir_source': '/input',
            'inputdir_target': '/share/incoming',
            'outputdir_source': '/output',
            'outputdir_target': '/share/outgoing'
        }

        # Call schedule_job
        result = manager.schedule_job(image, command, name, resources_dict, env, uid, gid, mounts_dict)

        # Verify that containers.run was called with only the first network
        mock_docker_client.containers.run.assert_called_once()
        call_args = mock_docker_client.containers.run.call_args
        assert call_args[1]['network'] == 'network1'

        # Verify that the second network was connected separately
        mock_docker_client.networks.get.assert_called_once_with('network2')
        mock_network.connect.assert_called_once_with(mock_container)

        assert result == mock_container

    def test_docker_networks_none(self):
        """Test that no network parameter is passed when DOCKER_NETWORKS is not configured."""
        config = {}
        mock_docker_client = Mock()

        with patch('docker.from_env', return_value=mock_docker_client):
            manager = DockerManager(config, mock_docker_client)

        # Mock the containers.run method
        mock_container = Mock()
        mock_docker_client.containers.run.return_value = mock_container

        # Test parameters
        image = 'test-image'
        command = ['test', 'command']
        name = 'test-job'
        resources_dict = {'number_of_workers': 1, 'cpu_limit': 1, 'memory_limit': 100, 'gpu_limit': 0}
        env = []
        uid = None
        gid = None
        mounts_dict = {
            'inputdir_source': '/input',
            'inputdir_target': '/share/incoming',
            'outputdir_source': '/output',
            'outputdir_target': '/share/outgoing'
        }

        # Call schedule_job
        result = manager.schedule_job(image, command, name, resources_dict, env, uid, gid, mounts_dict)

        # Verify that containers.run was called without network parameter
        mock_docker_client.containers.run.assert_called_once()
        call_args = mock_docker_client.containers.run.call_args
        assert 'network' not in call_args[1]
        assert result == mock_container