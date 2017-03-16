-- MySQL dump 10.13  Distrib 5.5.53, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: eve
-- ------------------------------------------------------
-- Server version	5.5.53-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `active_nodes`
--

DROP TABLE IF EXISTS `active_nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `active_nodes`
--

LOCK TABLES `active_nodes` WRITE;
/*!40000 ALTER TABLE `active_nodes` DISABLE KEYS */;
/*!40000 ALTER TABLE `active_nodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `active_topologies`
--

DROP TABLE IF EXISTS `active_topologies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `active_topologies` (
  `src_id` int(11) NOT NULL,
  `src_if` int(11) NOT NULL,
  `dst_id` int(11) NOT NULL,
  `dst_if` int(11) NOT NULL,
  PRIMARY KEY (`src_id`,`src_if`,`dst_id`,`dst_if`),
  KEY `dst_id` (`dst_id`),
  CONSTRAINT `active_topologies_ibfk_1` FOREIGN KEY (`src_id`) REFERENCES `active_nodes` (`label`),
  CONSTRAINT `active_topologies_ibfk_2` FOREIGN KEY (`dst_id`) REFERENCES `active_nodes` (`label`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `active_topologies`
--

LOCK TABLES `active_topologies` WRITE;
/*!40000 ALTER TABLE `active_topologies` DISABLE KEYS */;
/*!40000 ALTER TABLE `active_topologies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `controllers`
--

DROP TABLE IF EXISTS `controllers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `controllers` (
  `id` int(11) NOT NULL,
  `inside_ip` varchar(255) NOT NULL,
  `outside_ip` varchar(255) NOT NULL,
  `master` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `controllers`
--

LOCK TABLES `controllers` WRITE;
/*!40000 ALTER TABLE `controllers` DISABLE KEYS */;
INSERT INTO `controllers` VALUES (0,'172.17.0.1','10.113.8.57',1);
/*!40000 ALTER TABLE `controllers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `labs`
--

DROP TABLE IF EXISTS `labs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `labs` (
  `id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `path` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`,`path`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `labs`
--

LOCK TABLES `labs` WRITE;
/*!40000 ALTER TABLE `labs` DISABLE KEYS */;
INSERT INTO `labs` VALUES ('011fbc72-3941-420f-bd44-f7925319562d','C360 cfg LAB08','C360 cfg LAB08.unl','/Imported'),('0cd807d2-8a6d-4e40-93a1-b2c83b5e0d15','A story about STP','A story about STP.unl','/InfoCert'),('1719eed8-638b-4090-bb53-5e6333e11cf8','Cisco 360 RSv5 TS08 Clean','Cisco 360 RSv5 TS08 Clean.unl','/Imported'),('23b9b679-93b1-48e7-b06d-7f79958fca5b','Cisco 360 RSv5 TS02 Clean','Cisco 360 RSv5 TS02 Clean.unl','/Imported'),('24175bf7-ed5f-4919-85fb-fb0978ed9896','C360 cfg LAB02','C360 cfg LAB02.unl','/Imported'),('3207cdab-a2f0-4cd3-b433-e1a74c7e8256','Cisco 360 RSv5 TS10 Clean','Cisco 360 RSv5 TS10 Clean.unl','/Imported'),('39c2b3c1-54d5-4bcb-8ab4-282bea96092b','Cisco 360 RSv5 TS01 Clean','Cisco 360 RSv5 TS01 Clean.unl','/Imported'),('4fbc6ff4-178f-40f9-a647-867a63f895ad','vrf','vrf.unl','/Andrea'),('54ad647b-c386-4bcb-b7ad-fe35e7b06a89','A story about BGP','A story about BGP.unl','/InfoCert'),('637a1150-c097-4dc7-afdb-0617aef0034c','bgp','bgp.unl','/Andrea'),('7760b2af-a9ae-42b2-ab5d-1096adde1067','Cisco 360 RSv5 TS04 Clean','Cisco 360 RSv5 TS04 Clean.unl','/Imported'),('80c33918-c5b3-4360-8775-443255f3fa2c','C360 cfg LAB06','C360 cfg LAB06.unl','/Imported'),('890acaef-d064-4748-954a-f18e4e0ab7f1','bgp','bgp.unl','/Leonardo'),('960f5f95-313d-4a6f-a040-b89395a2e6f4','test ospf','test ospf.unl','/'),('9a2af455-e83b-49e5-9f74-e830167f8daa','C360 cfg LAB09','C360 cfg LAB09.unl','/Imported'),('9ca1f9b1-6535-4216-95f2-3ba9f5a61091','C360 cfg LAB01','C360 cfg LAB01.unl','/Imported'),('9e013b9d-1482-46e1-af3d-445e34eb4c88','360 TS RS v5','360 TS RS v5.unl','/Imported'),('a2625056-1f17-4331-99e8-ea67e0a7f93b','C360 cfg LAB03','C360 cfg LAB03.unl','/Imported'),('a4ed2c7b-5f98-4a24-a160-2c5e5a6620a5','Cisco 360 RSv5 TS05 Clean','Cisco 360 RSv5 TS05 Clean.unl','/Imported'),('a9a500e0-bab3-4801-90ae-2260b29724e5','nat','nat.unl','/Andrea'),('ac658f03-8748-4432-815e-d43263782bbe','test','test.unl','/Leonardo'),('b2035473-2e53-4594-ab4e-76f73dff62cf','Twice NAT on Cisco IOS routers','Twice NAT on Cisco IOS routers.unl','/Andrea'),('c843cd00-4549-463a-b7ae-7bdf3639a529','C360 cfg LAB04','C360 cfg LAB04.unl','/Imported'),('c8b97294-95ec-4d70-84dc-1de0be3a6d3d','Cisco 360 RSv5 TS07 Clean','Cisco 360 RSv5 TS07 Clean.unl','/Imported'),('cc492849-42e5-44a8-b07d-8e253b3fe1a7','Cisco 360 RSv5 TS09 Clean','Cisco 360 RSv5 TS09 Clean.unl','/Imported'),('dd27b84d-c013-41de-ba69-4d4c34951ffd','OTV Legacy','OTV Legacy.unl','/Andrea'),('e0c04fb3-3516-443e-a2d9-599f36f359c8','C360 cfg LAB10','C360 cfg LAB10.unl','/Imported'),('e0f28ca8-e2c8-47d4-8f2e-7a4c036e781d','Cisco 360 RSv5 TS03 Clean','Cisco 360 RSv5 TS03 Clean.unl','/Imported'),('ec34f1fb-93b2-4014-a5c8-f0be8aa842f2','VMware NSX','VMware NSX.unl','/Andrea'),('edf35947-a0d8-4f6b-a27d-0ae411d84643','Cisco 360 RSv5 TS06 Clean','Cisco 360 RSv5 TS06 Clean.unl','/Imported'),('f7211054-02df-484f-af7c-410f817f9fa9','Checkpoint','Checkpoint.unl','/Andrea'),('f77509ae-b66b-4c01-8794-738fca75380a','LabBGP','LabBGP.unl','/Matteo'),('f952334a-a24d-4283-927b-4fd6c306ba95','C360 cfg LAB05','C360 cfg LAB05.unl','/Imported'),('fcc087c2-5165-4845-adea-a9d024eeaf00','C360 cfg LAB07','C360 cfg LAB07.unl','/Imported');
/*!40000 ALTER TABLE `labs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roles` (
  `role` varchar(255) NOT NULL,
  `access_to` varchar(255) DEFAULT NULL,
  `can_write` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES ('admin','.*',1),('user','^/Andrea',1);
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles_to_users`
--

DROP TABLE IF EXISTS `roles_to_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roles_to_users` (
  `role` varchar(255) NOT NULL,
  `username` varchar(255) NOT NULL,
  PRIMARY KEY (`role`,`username`),
  KEY `username` (`username`),
  CONSTRAINT `roles_2_users_ibfk_1` FOREIGN KEY (`username`) REFERENCES `users` (`username`),
  CONSTRAINT `roles_2_users_ibfk_2` FOREIGN KEY (`role`) REFERENCES `roles` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles_to_users`
--

LOCK TABLES `roles_to_users` WRITE;
/*!40000 ALTER TABLE `roles_to_users` DISABLE KEYS */;
INSERT INTO `roles_to_users` VALUES ('admin','admin'),('user','andrea');
/*!40000 ALTER TABLE `roles_to_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('admin','admin@example.com',-1,'Default Administrator','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',0),('andrea','adainese@example.com',-1,'dainese','8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',200);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-03-13 14:43:44
