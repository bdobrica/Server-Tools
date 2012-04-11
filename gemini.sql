-- MySQL dump 10.11
--
-- Host: localhost    Database: gemini
-- ------------------------------------------------------
-- Server version	5.0.51a-24+lenny3-log

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
-- Table structure for table `files`
--

DROP TABLE IF EXISTS `files`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `files` (
  `id` int(11) NOT NULL auto_increment,
  `path` text NOT NULL,
  `pathhash` varchar(32) NOT NULL default '',
  `conthash` varchar(32) NOT NULL default '',
  `stamp` int(11) NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `pathhash` (`pathhash`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `records`
--

DROP TABLE IF EXISTS `records`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `records` (
  `id` int(11) NOT NULL auto_increment,
  `name` tinytext NOT NULL,
  `type` varchar(6) NOT NULL default 'A',
  `value` tinytext NOT NULL,
  `zoneid` int(11) NOT NULL default '0',
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `records`
--

LOCK TABLES `records` WRITE;
/*!40000 ALTER TABLE `records` DISABLE KEYS */;
INSERT INTO `records` VALUES (1,'coretarget.ro.','A','78.46.66.251',1),(2,'kernel','A','78.46.66.251',1),(3,'nucleus','A','178.63.71.5',1),(4,'*','CNAME','kernel',1);

/*!40000 ALTER TABLE `records` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vhosts`
--

DROP TABLE IF EXISTS `vhosts`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `vhosts` (
  `id` int(11) NOT NULL auto_increment,
  `server` tinytext NOT NULL,
  `alias` tinytext NOT NULL,
  `rewrite` text NOT NULL,
  `nginxrw` text NOT NULL,
  `options` int(2) NOT NULL default '5',
  `overide` int(2) NOT NULL default '0',
  `stats` int(1) NOT NULL default '0',
  `uid` int(4) NOT NULL default '81',
  `gid` int(4) NOT NULL default '81',
  `nodes` tinytext NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `vhosts`
--

LOCK TABLES `vhosts` WRITE;
/*!40000 ALTER TABLE `vhosts` DISABLE KEYS */;
INSERT INTO `vhosts` VALUES (1,'nucleus.coretarget.ro','','','[wp]',0,0,0,1001,1001,'nucleus');
/*!40000 ALTER TABLE `vhosts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `zones`
--

DROP TABLE IF EXISTS `zones`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `zones` (
  `id` int(11) NOT NULL auto_increment,
  `zone` tinytext NOT NULL,
  `serial` varchar(9) NOT NULL default '200601011',
  `refresh` int(11) NOT NULL default '28800',
  `retry` int(11) NOT NULL default '7200',
  `expire` int(11) NOT NULL default '604800',
  `minimum` int(11) NOT NULL default '86400',
  `nameserver` tinytext NOT NULL,
  `email` tinytext NOT NULL,
  `nodes` tinytext NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `zone` (`zone`(32))
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `zones`
--

LOCK TABLES `zones` WRITE;
/*!40000 ALTER TABLE `zones` DISABLE KEYS */;
INSERT INTO `zones` VALUES (1,'coretarget.ro','201004271',28800,7200,604800,86400,'nucleus.coretarget.ro','support.coretarget.ro','kernel');
/*!40000 ALTER TABLE `zones` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2010-04-28  7:30:43
