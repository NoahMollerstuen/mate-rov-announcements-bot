import json
from enum import Enum
import logging


class RuleType(Enum):
    SUBSTRING = "substring"


class FilterRule:
    def __init__(self, rule_type: RuleType) -> None:
        self.rule_type = rule_type

    def applyRule(self, line: str) -> bool:
        """
        Evaluate a changed line in a diff against the rule. A return value of True indicated the line should be ignored
        """
        raise NotImplementedError()


class SubstringFilterRule(FilterRule):
    def __init__(self, filter_string: str):
        super().__init__(RuleType.SUBSTRING)
        self.filter_string = filter_string

    def applyRule(self, line):
        return self.filter_string in line


class UpdateFilter:
    def __init__(self):
        self.rules: list[FilterRule] = []

    def addRule(self, rule: FilterRule):
        self.rules.append(rule)

    @classmethod
    def from_file(cls, file_path: str):
        """Load update blacklist from json"""

        update_filter = cls()

        try:
            with open(file_path, 'r') as json_file:
                blacklist_raw = json.load(json_file)
                if not isinstance(blacklist_raw, list):
                    raise ValueError

                for rule_dict in blacklist_raw:
                    if not isinstance(rule_dict, dict):
                        raise ValueError
                    
                    raw_type = rule_dict["type"]
                    filter_type = RuleType(raw_type)

                    if filter_type == RuleType.SUBSTRING:
                        new_rule = SubstringFilterRule(rule_dict["filter_string"])
                    # More rule types here
                    update_filter.addRule(new_rule)

        except FileNotFoundError:
            logging.warning(f"Failed to open {file_path}")
        except (json.decoder.JSONDecodeError, ValueError, KeyError):
            logging.warning(f"Failed to parse {file_path}")

        return update_filter


    def apply_filter(self, line: str) -> bool:
        for rule in self.rules:
            if rule.applyRule(line):
                return True
        return False


UpdateFilter.from_file("update_blacklist.json")
