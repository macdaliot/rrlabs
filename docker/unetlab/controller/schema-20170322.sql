/* Initial schema */
CREATE TABLE `controllers` (
  `id` int(11) NOT NULL,
  `inside_ip` varchar(255) NOT NULL,
  `outside_ip` varchar(255) NOT NULL,
  `master` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `labs` (
  `id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `path` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`,`path`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `roles` (
  `role` varchar(255) NOT NULL,
  `access_to` varchar(255) DEFAULT NULL,
  `can_write` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
INSERT INTO `roles` VALUES ('admin','.*',1);

CREATE TABLE `users` (
  `username` varchar(255) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `expiration` int(11) DEFAULT '-1',
  `name` varchar(255) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `labels` int(11) DEFAULT NULL,
  PRIMARY KEY (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
INSERT INTO `users` VALUES ('admin','admin@example.com',-1,'Default Administrator','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',0);

CREATE TABLE `active_nodes` (
  `username` varchar(255) NOT NULL,
  `lab_id` varchar(255) NOT NULL,
  `node_id` int(11) NOT NULL,
  `state` varchar(255) NOT NULL DEFAULT 'off',
  `label` int(11) NOT NULL AUTO_INCREMENT,
  `controller` int(11) NOT NULL,
  PRIMARY KEY (`username`,`lab_id`,`node_id`),
  UNIQUE KEY `label` (`label`),
  UNIQUE KEY `label_2` (`label`),
  KEY `lab_id` (`lab_id`),
  KEY `controller` (`controller`),
  CONSTRAINT `active_nodes_ibfk_1` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`id`),
  CONSTRAINT `active_nodes_ibfk_2` FOREIGN KEY (`username`) REFERENCES `users` (`username`),
  CONSTRAINT `active_nodes_ibfk_3` FOREIGN KEY (`controller`) REFERENCES `controllers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=245 DEFAULT CHARSET=utf8;

CREATE TABLE `active_topologies` (
  `src_id` int(11) NOT NULL,
  `src_if` int(11) NOT NULL,
  `dst_id` int(11) NOT NULL,
  `dst_if` int(11) NOT NULL,
  `lab_id` varchar(255) NOT NULL,
  `username` varchar(255) NOT NULL,
  PRIMARY KEY (`src_id`,`src_if`,`dst_id`,`dst_if`),
  KEY `dst_id` (`dst_id`),
  KEY `active_topologies_ibfk_3` (`lab_id`),
  KEY `active_topologies_ibfk_4` (`username`),
  CONSTRAINT `active_topologies_ibfk_1` FOREIGN KEY (`src_id`) REFERENCES `active_nodes` (`label`),
  CONSTRAINT `active_topologies_ibfk_2` FOREIGN KEY (`dst_id`) REFERENCES `active_nodes` (`label`),
  CONSTRAINT `active_topologies_ibfk_3` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`id`),
  CONSTRAINT `active_topologies_ibfk_4` FOREIGN KEY (`username`) REFERENCES `users` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `roles_to_users` (
  `role` varchar(255) NOT NULL,
  `username` varchar(255) NOT NULL,
  PRIMARY KEY (`role`,`username`),
  KEY `username` (`username`),
  CONSTRAINT `roles_2_users_ibfk_1` FOREIGN KEY (`username`) REFERENCES `users` (`username`),
  CONSTRAINT `roles_2_users_ibfk_2` FOREIGN KEY (`role`) REFERENCES `roles` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
INSERT INTO `roles_to_users` VALUES ('admin','admin');

