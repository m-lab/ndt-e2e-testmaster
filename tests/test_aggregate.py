# Copyright 2016 Measurement Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import unittest

from testmaster import aggregate


class AggregateTest(unittest.TestCase):

    def test_aggregate_single_value(self):
        aggregate_stats = aggregate.aggregate([5.0])
        self.assertAlmostEqual(5.0, aggregate_stats.minimum)
        self.assertAlmostEqual(5.0, aggregate_stats.maximum)
        self.assertAlmostEqual(5.0, aggregate_stats.mean)
        self.assertAlmostEqual(5.0, aggregate_stats.median)
        self.assertAlmostEqual(0.0, aggregate_stats.standard_deviation)
        self.assertEqual(1, aggregate_stats.sample_count)

    def test_aggregate_three_values(self):
        aggregate_stats = aggregate.aggregate([0.0, 10.0, 14.0])
        self.assertAlmostEqual(0.0, aggregate_stats.minimum)
        self.assertAlmostEqual(14.0, aggregate_stats.maximum)
        self.assertAlmostEqual(8.0, aggregate_stats.mean)
        self.assertAlmostEqual(10.0, aggregate_stats.median)
        self.assertAlmostEqual(5.8878405775518976,
                               aggregate_stats.standard_deviation)
        self.assertEqual(3, aggregate_stats.sample_count)

    def test_aggregate_ignores_None_values(self):
        """aggregate function should ignore None values."""
        aggregate_stats = aggregate.aggregate([0.0, 10.0, None, 14.0])
        self.assertAlmostEqual(0.0, aggregate_stats.minimum)
        self.assertAlmostEqual(14.0, aggregate_stats.maximum)
        self.assertAlmostEqual(8.0, aggregate_stats.mean)
        self.assertAlmostEqual(10.0, aggregate_stats.median)
        self.assertAlmostEqual(5.8878405775518976,
                               aggregate_stats.standard_deviation)
        self.assertEqual(3, aggregate_stats.sample_count)
