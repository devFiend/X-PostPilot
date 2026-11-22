"""
TweetDNA Trend Pulse & Breaking Niche News Radar.
Monitors Hacker News, GitHub Trending, and X niche curators to detect emerging conversations.
"""

from postpilot.trends.collector import TrendPulseCollector
from postpilot.trends.analyzer import TrendPulseAnalyzer
from postpilot.trends.generator import TrendTweetGenerator

__all__ = ["TrendPulseCollector", "TrendPulseAnalyzer", "TrendTweetGenerator"]
